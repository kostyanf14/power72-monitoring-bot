import asyncio
import logging
import threading
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import RPi.GPIO as GPIO

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
class StatusModel:
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
    normal: StatusModel
    standby: StatusModel


class Status(metaclass=SingletonMeta):
    power_statuses: list[StatusModel]
    ats_statuses: list[ATSStatus]
    stop_sync_event: threading.Event
    sync_thread: threading.Thread
    on_update: Callable[[], Coroutine[Any, Any, None]]

    def init(self):
        logger.info("Initializing Status class")

        GPIO.setmode(GPIO.BCM)

        self.power_statuses = [
            StatusModel(False, 'Network', 17, False),
            StatusModel(False, 'Generator', 27, False),
            StatusModel(False, 'Kitchen', 22, False),
        ]

        self.ats_statuses = [
            ATSStatus(
                StatusModel(False, "Network", 25, True),
                StatusModel(False, "Generator", 24, True),
            ),
            ATSStatus(
                StatusModel(False, "NetworkInternal", 16, True),
                StatusModel(False, "Battery", 23, True),
            )
        ]

        for power in self.power_statuses:
            GPIO.setup(power.gpio_port, GPIO.IN)

        for ats in self.ats_statuses:
            GPIO.setup(ats.normal.gpio_port, GPIO.IN)
            GPIO.setup(ats.standby.gpio_port, GPIO.IN)

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
