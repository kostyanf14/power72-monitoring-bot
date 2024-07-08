from dataclasses import dataclass

import RPi.GPIO as GPIO


@dataclass
class GPIOStatus:
    gpio_status: bool
    name: str
    gpio_port: int
    gpio_hight_mode: bool
    report_on_change: bool

    def update_status(self) -> bool:
        updated = False

        next_status = GPIO.input(self.gpio_port)
        if self.gpio_status != next_status:
            self.gpio_status = next_status
            if self.report_on_change:
                updated = True

        return updated

    def text_status(self) -> list[tuple[str, str]]:
        return [(self.name, '✅' if self.fixed_status else '❌')]

    @property
    def fixed_status(self):
        return self.gpio_status if self.gpio_hight_mode else not self.gpio_status
