import threading
from typing import Callable, Dict, List
from src.runtime.runtime_models import SensorEvent, SensorEventType


class SensorBus:
    """
    Thread-safe publish-subscribe event bus decoupling hardware sensors from perception.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[SensorEventType, List[Callable[[SensorEvent], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: SensorEventType, callback: Callable[[SensorEvent], None]) -> None:
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def publish(self, event: SensorEvent) -> None:
        with self._lock:
            callbacks = list(self._subscribers.get(event.event_type, []))

        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                print(f"[SensorBus] Subscriber error: {e}")

    def clear(self) -> None:
        with self._lock:
            self._subscribers.clear()
