"""A controllable clock for deterministic, time-dependent scenarios."""

from __future__ import annotations

from datetime import datetime, timedelta


class SimulatedClock:
    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, minutes: float = 0, hours: float = 0, days: float = 0) -> datetime:
        self.now = self.now + timedelta(minutes=minutes, hours=hours, days=days)
        return self.now
