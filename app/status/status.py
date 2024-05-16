import asyncio
import math
import logging
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import RPi.GPIO as GPIO
from ina219 import INA219

from app.utils import SingletonMeta

logger = logging.getLogger(__name__)
# 220 фіолетовий/сірий жовтий 5в11 GPIO25
# Генератор жовтий/помаранчевий коричневий 5в9 GPIO24
# 2202 синій/зелений помаранчевий 33в16 GPIO16
# УПС помаранчевий/жовтий рожевий 5в8 GPIO23

# 220v -> 17
# 220v -> 27
# 220v -> 22


@dataclass
class GPIOStatusModel:
    status: bool
    name: str
    gpio_port: int
    gpio_hight_mode: bool

    def update_status(self) -> bool:
        updated = False

        next_status = GPIO.input(self.gpio_port)
        if self.status != next_status:
            updated = True
            self.status = next_status

        return updated

    @property
    def fixed_status(self):
        return self.status if self.gpio_hight_mode else not self.status


@dataclass
class ATSStatus:
    normal: GPIOStatusModel
    standby: GPIOStatusModel


@dataclass
class VoltageStatus:
    voltage: float
    name: str
    shunt_ohms: float
    address: int

    __ina: INA219
    __reported_voltage_percent: float

    def __init__(self, voltage: float, name: str, shunt_ohms: float, address: int):
        self.voltage = voltage
        self.name = name
        self.shunt_ohms = shunt_ohms
        self.address = address

        self.__ina = INA219(shunt_ohms, busnum=0x1, address=address)
        self.__ina.configure()
        self.__reported_voltage_percent = 0

    def percent(self) -> float:
        a = 13.3
        b = 39.25
        c = 13

        return max(-1, 100 - math.exp(a - 5 * self.voltage) - math.exp(b - 3 * self.voltage) - math.exp(c-self.voltage))

    def update_status(self) -> bool:
        updated = False

        voltage_status = self.__ina.voltage()
        self.voltage = voltage_status

        delta = self.__reported_voltage_percent - self.percent()
        if abs(delta) > 10:
            self.__reported_voltage_percent = self.percent()
            updated = True

        return updated


class Status(metaclass=SingletonMeta):
    power_statuses: list[GPIOStatusModel]
    ats_statuses: list[ATSStatus]
    voltage_statuses: list[VoltageStatus]
    on_update: Callable[[], Coroutine[Any, Any, None]]
    __ina: INA219

    def init(self):
        logger.info("Initializing Status class")

        GPIO.setmode(GPIO.BCM)

        self.power_statuses = [
            GPIOStatusModel(False, 'Network', 22, False),
            GPIOStatusModel(False, 'Generator', 17, False),
            GPIOStatusModel(False, 'Kitchen', 27, False),
        ]

        self.ats_statuses = [
            ATSStatus(
                GPIOStatusModel(False, "Network", 25, True),
                GPIOStatusModel(False, "Generator", 24, True),
            ),
            ATSStatus(
                GPIOStatusModel(False, "NetworkInternal", 16, True),
                GPIOStatusModel(False, "Battery", 23, True),
            )
        ]

        self.voltage_statuses = [
            VoltageStatus(0, "Battery", 0.1, 0x40)
        ]

        for power in self.power_statuses:
            GPIO.setup(power.gpio_port, GPIO.IN)

        for ats in self.ats_statuses:
            GPIO.setup(ats.normal.gpio_port, GPIO.IN)
            GPIO.setup(ats.standby.gpio_port, GPIO.IN)

        self.sync_status()

    def start_monitoring(self, on_update: Callable[[], Coroutine[Any, Any, None]]) -> None:
        logger.info("Starting monitoring")
        loop = asyncio.get_event_loop()
        loop.create_task(self.__sync_status())
        self.on_update = on_update

    def sync_status(self) -> bool:
        logger.debug("Syncing status")
        updated = False

        for power in self.power_statuses:
            updated |= power.update_status()

        for ats in self.ats_statuses:
            updated |= ats.normal.update_status()
            updated |= ats.standby.update_status()

        for voltage in self.voltage_statuses:
            updated |= voltage.update_status()

        return updated

    # Power ⚡️
    #   Main        ✅
    #   Generator   ❌
    #   Battery     ✅
    # Status
    #   ATS1        Generator
    #   ATS2        Battery
    #   Battery     12.3v (~90%)
    def generate_status_msg(self) -> str:
        lines = []

        lines.append('```')
        lines.append("Power ⚡️")
        for power_id in range(len(self.power_statuses)):
            power = self.power_statuses[power_id]
            lines.append(f"   {power.name:10} {'✅' if power.fixed_status else '❌'}")

        lines.append("Status:")
        for ats_id in range(len(self.ats_statuses)):
            ats = self.ats_statuses[ats_id]
            enabled = []
            if ats.normal.fixed_status:
                enabled.append(ats.normal.name)
            if ats.standby.fixed_status:
                enabled.append(ats.standby.name)

            if len(enabled) == 2:
                lines.append(f"   ATS{ats_id + 1}       ❌*{enabled[0]} & {enabled[1]}*❌")
            elif len(enabled) == 0:
                lines.append(f"   ATS{ats_id + 1}       ❌")
            else:
                lines.append(f"   ATS{ats_id + 1}       {enabled[0]}")

        for v_id in range(len(self.voltage_statuses)):
            voltage = self.voltage_statuses[v_id]
            lines.append(f"   {voltage.name}       {voltage.voltage} (~{voltage.percent()}%)")

        lines.append('```')
        return "\n".join(lines)

    async def __sync_status(self):
        while True:
            if self.sync_status():
                try:
                    await self.on_update()
                except Exception as err:
                    logger.error("Error during on_update(): %s", err)
            await asyncio.sleep(5)
