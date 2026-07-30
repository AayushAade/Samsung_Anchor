"""
MEMORA Ontology Manager.

Maintains deterministic inheritance taxonomies across entity and relationship concepts:
- Person / Caregiver / Patient -> Entity
- Medication -> Healthcare -> Clinical Object -> Entity
- Room -> Location -> Entity
"""

from __future__ import annotations

from typing import Dict, List, Set

from src.knowledge.knowledge_models import EntityType


class OntologyManager:
    """
    Deterministic concept ontology and taxonomy inheritance manager.
    """

    TAXONOMY: Dict[str, List[str]] = {
        "PATIENT": ["PERSON", "ENTITY"],
        "CAREGIVER": ["PERSON", "ENTITY"],
        "PERSON": ["ENTITY"],
        "MEDICATION": ["HEALTHCARE_ITEM", "CLINICAL_OBJECT", "ENTITY"],
        "OBJECT": ["ENTITY"],
        "ROOM": ["LOCATION", "SPATIAL_ENTITY", "ENTITY"],
        "LOCATION": ["SPATIAL_ENTITY", "ENTITY"],
        "ROUTINE": ["TEMPORAL_CONCEPT", "ENTITY"],
        "REMINDER": ["NOTIFICATION", "ENTITY"],
        "APPOINTMENT": ["TEMPORAL_CONCEPT", "ENTITY"],
        "DEVICE": ["OBJECT", "ENTITY"],
    }

    @classmethod
    def get_ancestors(cls, entity_type: EntityType) -> List[str]:
        return cls.TAXONOMY.get(entity_type.value, ["ENTITY"])

    @classmethod
    def is_subclass_of(cls, child_type: EntityType, parent_type_name: str) -> bool:
        ancestors = cls.get_ancestors(child_type)
        return parent_type_name.upper() in ancestors or child_type.value == parent_type_name.upper()
