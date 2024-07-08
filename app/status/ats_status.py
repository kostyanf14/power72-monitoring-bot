from dataclasses import dataclass

from app.status.gpio_status import GPIOStatus


@dataclass
class ATSStatus:
    name: str
    normal: GPIOStatus
    standby: GPIOStatus

    def update_status(self) -> bool:
        updated = False

        updated |= self.normal.update_status()
        updated |= self.standby.update_status()

        return updated

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
