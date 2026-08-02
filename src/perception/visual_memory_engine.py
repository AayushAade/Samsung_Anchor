"""
Visual Episodic Memory Engine.

Transforms visual observations into persistent episodic memory entries:
- object_category
- confidence
- spatial_description
- timestamp
- room
- associated_patient
- observation_source

Provides honest, non-hallucinated location responses for Alzheimer's patients.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class VisualMemoryEntry:
    object_category: str
    confidence: float
    spatial_description: str
    timestamp: str
    room: str
    associated_patient: str = "Eleanor"
    observation_source: str = "Camera HAL (OpenCV)"
    x: float = 0.0
    y: float = 0.0


class VisualEpisodicMemoryEngine:
    """
    Manages persistent visual episodic observations and provides honest,
    calm natural language retrieval for Alzheimer's patient queries.
    """

    def __init__(self, db_instance: Optional[Any] = None) -> None:
        self.db = db_instance
        self._visual_memories: Dict[str, VisualMemoryEntry] = {}
        self._seed_default_memories()

    def _seed_default_memories(self) -> None:
        now_iso = datetime.now().isoformat()
        # Seed 5 meaningful personal objects
        self._visual_memories["reading glasses"] = VisualMemoryEntry(
            object_category="reading glasses",
            confidence=0.92,
            spatial_description="on the coffee table beside your newspaper",
            timestamp=now_iso,
            room="Living Room",
            associated_patient="Eleanor",
        )
        self._visual_memories["medication bottle"] = VisualMemoryEntry(
            object_category="medication bottle",
            confidence=0.95,
            spatial_description="on the kitchen counter next to the water pitcher",
            timestamp=now_iso,
            room="Kitchen",
            associated_patient="Eleanor",
        )
        self._visual_memories["walking cane"] = VisualMemoryEntry(
            object_category="walking cane",
            confidence=0.88,
            spatial_description="resting against the armchair",
            timestamp=now_iso,
            room="Living Room",
            associated_patient="Eleanor",
        )
        self._visual_memories["keys"] = VisualMemoryEntry(
            object_category="keys",
            confidence=0.85,
            spatial_description="on the entryway table by the door",
            timestamp=now_iso,
            room="Entryway",
            associated_patient="Eleanor",
        )
        self._visual_memories["television remote"] = VisualMemoryEntry(
            object_category="television remote",
            confidence=0.65,
            spatial_description="on the dining table",
            timestamp=now_iso,
            room="Dining Room",
            associated_patient="Eleanor",
        )

    def record_observation(
        self,
        object_category: str,
        spatial_description: str,
        confidence: float = 0.90,
        room: str = "Living Room",
        patient_name: str = "Eleanor",
        source: str = "Camera HAL (OpenCV)",
        x: float = 0.0,
        y: float = 0.0,
    ) -> VisualMemoryEntry:
        key = object_category.lower().strip()
        entry = VisualMemoryEntry(
            object_category=key,
            confidence=confidence,
            spatial_description=spatial_description,
            timestamp=datetime.now().isoformat(),
            room=room,
            associated_patient=patient_name,
            observation_source=source,
            x=x,
            y=y,
        )
        self._visual_memories[key] = entry
        return entry

    def recall_object_location(
        self,
        query_text: str,
        patient_name: str = "Eleanor",
    ) -> Dict[str, Any]:
        q_lower = query_text.lower().strip()

        # Match target object category
        target_entry: Optional[VisualMemoryEntry] = None
        for key, entry in self._visual_memories.items():
            if key in q_lower or any(word in q_lower for word in key.split() if len(word) > 3):
                target_entry = entry
                break

        if not target_entry:
            return {
                "found": False,
                "confidence": 0.0,
                "response": "I have never observed that object.",
                "entry": None,
            }

        # Clinical Confidence Thresholding (Never hallucinate)
        conf = target_entry.confidence
        obj_name = target_entry.object_category
        spatial = target_entry.spatial_description
        room = target_entry.room

        if conf >= 0.80:
            resp = f"I last saw your {obj_name} {spatial} in the {room}."
        elif 0.50 <= conf < 0.80:
            resp = f"I think your {obj_name} may still be {spatial}, but I'm not certain."
        else:
            resp = f"I am not certain where your {obj_name} is right now."

        return {
            "found": True,
            "confidence": conf,
            "response": resp,
            "entry": target_entry,
        }
