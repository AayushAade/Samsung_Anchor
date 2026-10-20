"""
Simulated battery for a portable/wearable MEMORA device.

This is a simulation only. MEMORA does not read the host computer's battery:
a laptop battery says nothing about a wearable device. Every reading is
labelled SIMULATED_BATTERY.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

LOW_PCT = 20.0
CRITICAL_PCT = 5.0
SOURCE = "SIMULATED_BATTERY"


@dataclass
class BatteryReading:
    level_pct: float
    charging: bool
    state: str  # OK | LOW | CRITICAL
    trend_pct_per_hour: float
    source: str = SOURCE


class SimulatedBattery:
    def __init__(self, clock: Callable[[], datetime], level_pct: float = 100.0,
                 drain_pct_per_hour: float = 8.0, charge_pct_per_hour: float = 40.0) -> None:
        self.clock = clock
        self.level = float(level_pct)
        self.charging = False
        self.drain = drain_pct_per_hour
        self.charge_rate = charge_pct_per_hour
        self._last = clock()
        self._announced: Optional[str] = None

    def set_level(self, level_pct: float) -> None:
        self._update()
        self.level = max(0.0, min(100.0, float(level_pct)))

    def set_charging(self, charging: bool) -> None:
        self._update()
        self.charging = charging

    def _update(self) -> None:
        now = self.clock()
        hours = max(0.0, (now - self._last).total_seconds() / 3600.0)
        self._last = now
        delta = (self.charge_rate if self.charging else -self.drain) * hours
        self.level = max(0.0, min(100.0, self.level + delta))

    def reading(self) -> BatteryReading:
        self._update()
        state = "CRITICAL" if self.level <= CRITICAL_PCT else "LOW" if self.level <= LOW_PCT else "OK"
        trend = self.charge_rate if self.charging else -self.drain
        return BatteryReading(round(self.level, 1), self.charging, state, trend)

    def notice(self) -> Optional[str]:
        """A one-time spoken notice when the battery first becomes LOW or CRITICAL."""
        r = self.reading()
        if r.charging or r.state == "OK":
            if r.state == "OK":
                self._announced = None
            return None
        if r.state == self._announced:
            return None
        self._announced = r.state
        if r.state == "CRITICAL":
            return (f"My battery is almost empty ({r.level_pct:.0f}%, simulated). I may switch off soon. "
                    "What you've told me is saved. Please charge me.")
        return f"My battery is getting low ({r.level_pct:.0f}%, simulated). Please charge me soon."
