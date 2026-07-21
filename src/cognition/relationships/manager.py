from typing import Dict, List, Optional, Any
from src.cognition.relationships.models import RelationshipProfile


class RelationshipManager:
    """
    Manages relationship profiles and performs shared memory ranking for the patient.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, RelationshipProfile] = {}
        self._seed_default_profiles()

    def _seed_default_profiles(self) -> None:
        """Seed default relationship profiles (e.g., Sarah)."""
        sarah_profile = RelationshipProfile(
            person_id="Face_1",
            name="Sarah",
            relationship="Daughter",
            preferred_greeting="Hello Sarah, so lovely to see you",
            visit_frequency="Twice weekly",
            last_interaction="2 days ago",
            shared_memories=[
                {
                    "summary": "Looked at family photo album together in the living room",
                    "recency": "High",
                    "importance": "CRITICAL",
                    "emotional_significance": "Warm & joyful",
                },
                {
                    "summary": "Sarah brought homemade apple pie last Tuesday",
                    "recency": "Medium",
                    "importance": "NORMAL",
                    "emotional_significance": "Comforting",
                },
            ],
            important_dates=["Birthday: October 14", "Graduation: May 20"],
            communication_preferences="Enjoys looking at photos, speak softly",
            care_notes="Sarah brings groceries on Tuesdays and helps with gardening",
            closeness_score=0.98,
        )
        self._profiles["Face_1"] = sarah_profile
        self._profiles["Sarah"] = sarah_profile

    def get_profile(
        self,
        person_id: str,
        name: Optional[str] = None,
        relationship: Optional[str] = None,
    ) -> Optional[RelationshipProfile]:
        """Fetch relationship profile by ID, name, or relationship fallback."""
        if person_id in self._profiles:
            return self._profiles[person_id]
        if name and name in self._profiles:
            return self._profiles[name]

        # Dynamic fallback for recognized person with no pre-seeded profile
        if name or relationship:
            return RelationshipProfile(
                person_id=person_id,
                name=name or "Family Member",
                relationship=relationship or "Loved One",
                preferred_greeting=f"Hello {name}" if name else "Hello",
                visit_frequency="Regular visitor",
                last_interaction="Recently",
                shared_memories=[],
                important_dates=[],
                communication_preferences="Warm and calm",
                care_notes="",
                closeness_score=0.85,
            )

        return None

    def register_profile(self, profile: RelationshipProfile) -> None:
        """Register or update a relationship profile."""
        self._profiles[profile.person_id] = profile
        if profile.name:
            self._profiles[profile.name] = profile

    def rank_shared_memories(
        self, memories: List[Any], person_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters and ranks memories relevant to the specific visitor by recency and importance.
        """
        ranked = []
        for mem in memories:
            summary = getattr(mem, "summary", str(mem))
            importance = getattr(mem, "importance", "NORMAL")
            importance_str = (
                importance.value if hasattr(importance, "value") else str(importance)
            )

            # Filter if person match
            mem_person = getattr(mem, "person", None)
            if person_name and mem_person and person_name.lower() not in str(mem_person).lower():
                continue

            ranked.append(
                {
                    "summary": summary,
                    "importance": importance_str,
                    "recency": "Recent",
                    "emotional_significance": "Meaningful",
                }
            )

        # Sort by importance heuristic
        importance_weights = {"CRITICAL": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
        ranked.sort(
            key=lambda x: importance_weights.get(x["importance"], 2), reverse=True
        )
        return ranked
