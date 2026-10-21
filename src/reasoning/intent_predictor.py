"""Habits, routines, and proactive context whispers (Pillar III)."""

from typing import Dict, List, Any
import time

class IntentPredictor:
    """
    Rule-based habit & routine learning engine (Objective 11).
    Tracks behavioral repetitions, frequently lost objects, and spatio-temporal routines.
    Persists learned patterns without requiring complex ML dependencies.
    """

    def __init__(self) -> None:
        self._lost_object_counts: Dict[str, int] = {}
        self._routine_counts: Dict[str, int] = {}
        self._room_visit_counts: Dict[str, int] = {}

    def record_lost_object_search(self, object_name: str) -> int:
        """
        Record when a patient searches for a lost object.
        If search count > 1, retrieval priority is automatically boosted.
        """
        obj_key = object_name.lower().strip()
        self._lost_object_counts[obj_key] = self._lost_object_counts.get(obj_key, 0) + 1
        count = self._lost_object_counts[obj_key]
        print(f"🧠 [Real Learning] Recorded search for '{obj_key}' (Count: {count}).")
        return count

    def record_routine_event(self, time_label: str, action_or_item: str) -> int:
        """
        Record routine occurrences (e.g., ("5 PM", "tea"), ("Morning", "medication")).
        """
        routine_key = f"{time_label.lower().strip()}:{action_or_item.lower().strip()}"
        self._routine_counts[routine_key] = self._routine_counts.get(routine_key, 0) + 1
        count = self._routine_counts[routine_key]
        print(f"🧠 [Real Learning] Learned routine pattern '{routine_key}' (Occurrences: {count}).")
        return count

    def record_room_visit(self, room_name: str, time_of_day: str) -> int:
        """
        Record spatial visitation patterns (e.g., ("Living Room", "Evening")).
        """
        visit_key = f"{room_name.lower().strip()}:{time_of_day.lower().strip()}"
        self._room_visit_counts[visit_key] = self._room_visit_counts.get(visit_key, 0) + 1
        count = self._room_visit_counts[visit_key]
        print(f"🧠 [Real Learning] Learned spatial pattern '{visit_key}' (Visits: {count}).")
        return count

    def get_retrieval_priority_boost(self, object_name: str) -> float:
        """
        Returns retrieval priority multiplier based on learned frequency.
        """
        obj_key = object_name.lower().strip()
        count = self._lost_object_counts.get(obj_key, 0)
        if count >= 3:
            return 2.5
        elif count >= 2:
            return 1.8
        elif count >= 1:
            return 1.2
        return 1.0

    def get_learned_patterns(self) -> Dict[str, Any]:
        """
        Summarizes all learned behavioral patterns.
        """
        frequently_lost = [k for k, v in self._lost_object_counts.items() if v >= 2]
        learned_routines = [k for k, v in self._routine_counts.items() if v >= 2]
        learned_spatial = [k for k, v in self._room_visit_counts.items() if v >= 2]
        
        return {
            "frequently_lost_objects": frequently_lost,
            "learned_routines": learned_routines,
            "learned_spatial_patterns": learned_spatial,
            "raw_object_counts": self._lost_object_counts,
            "raw_routine_counts": self._routine_counts,
            "raw_spatial_counts": self._room_visit_counts,
        }

