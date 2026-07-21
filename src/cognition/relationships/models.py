from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RelationshipProfile:
    """
    Detailed relationship profile for a known person in the patient's life.
    """
    person_id: str
    name: str
    relationship: str
    preferred_greeting: str = ""
    visit_frequency: str = "Weekly"
    last_interaction: str = "Recently"
    shared_memories: List[Dict[str, Any]] = field(default_factory=list)
    important_dates: List[str] = field(default_factory=list)
    communication_preferences: str = "Warm, gentle, and unhurried"
    care_notes: str = ""
    closeness_score: float = 0.95


@dataclass
class SocialContext:
    """
    Context provided by the SocialContextProvider during a cognitive cycle.
    """
    active_profile: Optional[RelationshipProfile] = None
    known_relationships_count: int = 0
    confidence: float = 1.0
