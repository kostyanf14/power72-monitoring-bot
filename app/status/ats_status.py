from dataclasses import dataclass
from typing import Tuple

from app.status.gpio_status import GPIOStatus


@dataclass
class ATSStatus:
    name: str
    normal: GPIOStatus
    standby: GPIOStatus

    def update_status(self) -> Tuple[bool, list[str]]:
        updated = False
        triggered_by = []

        upd1, trb1 = self.normal.update_status()
        updated |= upd1
        triggered_by.extend(trb1)

        upd2, trb2 = self.standby.update_status()
        updated |= upd2
        triggered_by.extend(trb2)

        if updated:
            triggered_by.append(self.name)
        return (updated, triggered_by)

    def text_status(self) -> list[tuple[str, str]]:
        enabled = []
        if self.normal.fixed_status:
            enabled.append(self.normal.name)
        if self.standby.fixed_status:
            enabled.append(self.standby.name)

        if len(enabled) == 2:
            return [(self.name, f"❌*{enabled[0]} & {enabled[1]}*❌")]
        elif len(enabled) == 0:
            return [(self.name, "❌")]
        else:
            return [(self.name, enabled[0])]
