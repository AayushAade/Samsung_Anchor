"""
MEMORA Runtime Task Scheduler.

Schedules and executes periodic operational tasks:
- Memory retention expiration flushes
- Subsystem health checks
- Performance metrics aggregation
"""

from __future__ import annotations

import threading
import time
from typing import Callable, List, Optional


class ScheduledTask:
    def __init__(self, name: str, interval_sec: float, callback: Callable[[], None]) -> None:
        self.name = name
        self.interval_sec = interval_sec
        self.callback = callback
        self.last_run_ts: float = 0.0


class RuntimeScheduler:
    """
    Non-blocking periodic operational scheduler.
    """

    def __init__(self) -> None:
        self._tasks: List[ScheduledTask] = []
        self._lock = threading.Lock()

    def add_task(self, name: str, interval_sec: float, callback: Callable[[], None]) -> None:
        with self._lock:
            self._tasks.append(ScheduledTask(name, interval_sec, callback))

    def tick(self, current_ts: float = 0.0) -> int:
        """
        Execute any tasks due for execution. Returns number of tasks executed.
        """
        now = current_ts or time.time()
        executed = 0
        with self._lock:
            for task in self._tasks:
                if now - task.last_run_ts >= task.interval_sec:
                    try:
                        task.callback()
                        task.last_run_ts = now
                        executed += 1
                    except Exception:
                        pass
        return executed
