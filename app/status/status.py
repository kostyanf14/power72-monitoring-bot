import asyncio
import json
import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Coroutine

import RPi.GPIO as GPIO
from ina219 import INA219

from app.status.ats_status import ATSStatus
from app.status.gpio_status import GPIOStatus
from app.status.json_status import JSONField, JSONStatus
from app.utils import SingletonMeta

logger = logging.getLogger(__name__)


@dataclass
class Voltage219Status:
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


@dataclass
class VoltageJSONStatus:
    voltage: float
    name: str
    file_name: str
    field_name: str
    min_voltage: float
    max_voltage: float

    __reported_voltage_percent: float

    def __init__(self, voltage: float, name: str, file_name: str, field_name: str, min_voltage: float, max_voltage: float):
        self.voltage = voltage
        self.name = name
        self.file_name = file_name
        self.field_name = field_name

        self.min_voltage = min_voltage
        self.max_voltage = max_voltage

        self.__reported_voltage_percent = 0

    def percent(self) -> float:
        return 100.0 * (self.voltage - self.min_voltage) / (self.max_voltage - self.min_voltage)

    def update_status(self) -> bool:
        updated = False

        voltage_status = 0
        try:
            with open(self.file_name, "r") as file:
                data = json.load(file)
                json_time = data['Timestamp']
                timestamp = datetime.utcfromtimestamp(json_time)
                voltage_status = data[self.field_name]

                logger.debug("Timestamp: %s, Voltage: %s", timestamp, voltage_status)
        except Exception as e:
            logger.error("Error reading file %s: %s", self.file_name, e)
            return False

        self.voltage = voltage_status

        delta = self.__reported_voltage_percent - self.percent()
        if abs(delta) > 10:
            self.__reported_voltage_percent = self.percent()
            updated = True

        return updated

    def str_status(self) -> str:
        return f"{self.voltage} (~{self.percent()}%)"


class Status(metaclass=SingletonMeta):
    statuses: dict[str, list[Any]]
    on_update: Callable[[], Coroutine[Any, Any, None]]

    def _create_gpio_status(self, status: dict):
        port = status.get("gpio_port")
        if port is None:
            raise ValueError("Can't create GPIO Status: gpio_port is not defined")

        if not isinstance(port, int):
            raise ValueError("Can't create GPIO Status: gpio_port is not int")

        GPIO.setup(port, GPIO.IN)

        return GPIOStatus(
            bool(status.get("initial")),
            str(status.get("name")),
            port,
            bool(status.get("gpio_hight_mode")),
            bool(status.get("report_on_change"))
        )

    def _create_ats_status(self, status: dict):
        status1_content = status.get("status1")
        status2_content = status.get("status2")
        if status1_content is None:
            logger.error("Cannot create ats status, status1 is not defined.")
            return None

        if status2_content is None:
            logger.error("Cannot create ats status, status2 is not defined.")
            return None

        status1 = self._create_status(status1_content)
        if status1 is None:
            logger.error("Cannot create status1, ats status is invalid.")
            return None

        status2 = self._create_status(status2_content)
        if status2 is None:
            logger.error("Cannot create status2, ats status is invalid.")
            return None

        name = status.get("name")
        if name is None:
            logger.error("Cannot create ats status, name is not defined.")
            return None

        return ATSStatus(name, status1, status2)

    def _create_json_field(self, field: dict):
        return JSONField(
            str(field.get("name")),
            str(field.get("field")),
            field.get("value"),
            str(field.get("unit")),
            bool(field.get("report_on_change")),
            field.get("report_on_change_value", None),
            bool(field.get("have_percent", False)),
            field.get("percent_min", None),
            field.get("percent_max", None),
            bool(field.get("report_on_percent", False))
        )

    def _create_json_status(self, status: dict):
        fields = status.get("fields")
        path = status.get("file_path")
        if fields is None:
            raise ValueError("Can't create JSON Status: fields are not defined")

        if path is None:
            raise ValueError("Can't create JSON Status: file_path is not defined")

        return JSONStatus(
            path,
            list(map(lambda field: self._create_json_field(field), fields))
        )

    def _create_status(self, status: dict):
        type_data = status.get("type")
        if type_data is None:
            raise ValueError("Status type is not defined")

        status_type = type_data.lower()
        match status_type:
            case "gpio":
                value = self._create_gpio_status(status)
            case "ats":
                value = self._create_ats_status(status)
            case "json":
                value = self._create_json_status(status)
            case _:
                value = None

        if value is None:
            logger.error("Failed to create status with type %s", status_type)

        return value

    def parse_config(self, config_path: str):
        config_data = json.load(open(config_path, "r"))
        self.statuses = defaultdict(list)
        self.statuses_fail = []

        statuses_list = config_data.get("statuses", [])
        for status in statuses_list:
            value = self._create_status(status)

            if value is None:
                self.statuses_fail.append(status.get("name"))
            else:
                self.statuses[status.get("group")].append(value)

    def init(self, config_path: str):
        logger.info("Initializing Status class")

        GPIO.setmode(GPIO.BCM)

        self.parse_config(config_path)

        return

        self.voltage_statuses = [
            Voltage219Status(0, "Battery", 0.1, 0x40),
            VoltageJSONStatus(0, "Inverter", "/tmp/inverter.json", "Battery_voltage", 21.7, 28.7),
        ]

        self.sync_status()

    def start_monitoring(self, on_update: Callable[[], Coroutine[Any, Any, None]]) -> None:
        logger.info("Starting monitoring")
        loop = asyncio.get_event_loop()
        loop.create_task(self.__sync_status())
        self.on_update = on_update

    def sync_status(self) -> bool:
        logger.debug("Syncing status")
        updated = False

        for _, statuses in self.statuses.items():
            for status in statuses:
                updated |= status.update_status()

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

        for group, statuses in self.statuses.items():
            lines.append(group)
            for status in statuses:
                for name, value in status.text_status():
                    lines.append(f"   {name:10}   {value}")

        # for v_id in range(len(self.voltage_statuses)):
        #     voltage = self.voltage_statuses[v_id]
        #     lines.append(f"   {voltage.name:12}  {voltage.voltage} (~{voltage.percent()}%)")

        if self.statuses_fail.__len__() > 0:
            lines.append("Failed to create statuses:")
            for status in self.statuses_fail:
                lines.append(f"   {status}")

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
