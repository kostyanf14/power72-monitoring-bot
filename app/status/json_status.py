import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class JSONField:
    name: str
    field: str
    value: Any
    unit: str
    report_on_change: bool
    report_on_change_value: Any
    have_percent: bool
    percent_min: Any
    percent_max: Any
    report_on_percent: bool


@dataclass
class JSONStatus:
    file_path: str
    fields: list[JSONField]
    last_reported_value: dict[str, Any] = field(default_factory=dict)

    def __init__(self, file_path: str, fields: list[JSONField]):
        self.last_reported_value = {}
        self.file_path = file_path
        self.fields = fields

        for j_field in self.fields:
            self.last_reported_value[j_field.name] = j_field.value

    def _percent(self, j_field: JSONField) -> float:
        return (j_field.value - j_field.percent_min) / (j_field.percent_max - j_field.percent_min) * 100

    def _percent_changed(self, j_field: JSONField) -> bool:
        if j_field.report_on_change_value is not None:
            if abs(self._percent(j_field) - self.last_reported_value[j_field.name]) >= j_field.report_on_change_value:
                logger.debug("Field %s value %s changed percent to %s and reported",
                             j_field.name, j_field.value, self._percent(j_field))
                self.last_reported_value[j_field.name] = self._percent(j_field)
                return True

            logger.debug("Field %s value %s changed percent to %s but not reported",
                         j_field.name, j_field.value, self._percent(j_field))
            return False

        if abs(self._percent(j_field) - self.last_reported_value[j_field.name]) >= 0.1:
            logger.debug("Field %s value %s changed percent to %s and reported",
                         j_field.name, j_field.value, self._percent(j_field))
            self.last_reported_value[j_field.name] = self._percent(j_field)
            return True

        logger.debug("Field %s value %s changed percent to %s but not reported",
                     j_field.name, j_field.value, self._percent(j_field))
        return False

    def _value_changed(self, j_field: JSONField) -> bool:
        if j_field.have_percent:
            return self._percent_changed(j_field)

        if j_field.value != self.last_reported_value[j_field.name]:
            if j_field.report_on_change_value is not None:
                if abs(j_field.value - self.last_reported_value[j_field.name]) >= j_field.report_on_change_value:
                    logger.debug("Field %s changed to %s and reported", j_field.name, j_field.value)
                    self.last_reported_value[j_field.name] = j_field.value
                    return True

                logger.debug("Field %s changed to %s but not reported", j_field.name, j_field.value)
                return False

            if j_field.value != self.last_reported_value[j_field.name]:
                if not j_field.report_on_change:
                    logger.debug("Field %s changed to %s but not reported", j_field.name, j_field.value)
                    return False

                self.last_reported_value[j_field.name] = j_field.value
                logger.debug("Field %s changed to %s and reported", j_field.name, j_field.value)
                return True

        logger.debug("Field %s not changed", j_field.name)
        return False

    def update_status(self) -> bool:
        updated = False

        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)

                for j_field in self.fields:
                    if j_field.field in data:
                        if j_field.value != data[j_field.field]:
                            j_field.value = data[j_field.field]
                            updated |= self._value_changed(j_field)
                    else:
                        logger.error("Field %s not found in file %s", j_field.field, self.file_path)

        except Exception as e:
            logger.error("Error reading file %s: %s", self.file_path, e)
            return False

        return updated

    def text_status(self) -> list[tuple[str, str]]:
        status = []
        for j_field in self.fields:
            if j_field.have_percent:
                status.append((j_field.name, f"{j_field.value}{j_field.unit} (~{self._percent(j_field):.2f}%)"))
            else:
                status.append((j_field.name, f"{j_field.value}{j_field.unit}"))

        return status
