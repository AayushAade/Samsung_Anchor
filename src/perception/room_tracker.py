from datetime import datetime
from typing import List
from src.perception.sensor_models import RoomLocation


class RoomTracker:
    """
    Room awareness and location transition tracker.
    """

    def __init__(self, initial_room: RoomLocation = RoomLocation.LIVING_ROOM) -> None:
        self._current_room = initial_room
        self._history: List[str] = [f"{initial_room.value} at {datetime.now().strftime('%H:%M:%S')}"]

    def set_room(self, new_room: RoomLocation) -> RoomLocation:
        if new_room != self._current_room:
            self._current_room = new_room
            self._history.append(f"{new_room.value} at {datetime.now().strftime('%H:%M:%S')}")
        return self._current_room

    def get_current_room(self) -> RoomLocation:
        return self._current_room

    def get_room_history(self) -> List[str]:
        return self._history[-5:]
