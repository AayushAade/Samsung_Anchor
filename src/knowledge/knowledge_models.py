"""
MEMORA Semantic Knowledge Data Models.

Provides unified value objects for:
- 11 Entity Types & Explicit Entities
- Directional, Versioned Relationship Types & Relationships
- Append-Only Semantic Facts & Provenance Records
- Knowledge Graph Traversal & Query Contracts
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EntityType(str, Enum):
    PERSON = "PERSON"
    CAREGIVER = "CAREGIVER"
    PATIENT = "PATIENT"
    MEDICATION = "MEDICATION"
    OBJECT = "OBJECT"
    ROOM = "ROOM"
    LOCATION = "LOCATION"
    ROUTINE = "ROUTINE"
    REMINDER = "REMINDER"
    APPOINTMENT = "APPOINTMENT"
    DEVICE = "DEVICE"


class RelationshipType(str, Enum):
    BELONGS_TO = "BELONGS_TO"
    LOCATED_IN = "LOCATED_IN"
    CONNECTED_TO = "CONNECTED_TO"
    REQUIRES = "REQUIRES"
    CONTAINS = "CONTAINS"
    PART_OF = "PART_OF"
    SCHEDULED_BEFORE = "SCHEDULED_BEFORE"
    SCHEDULED_AFTER = "SCHEDULED_AFTER"
    MANAGED_BY = "MANAGED_BY"
    INTERACTS_WITH = "INTERACTS_WITH"


@dataclass
class Entity:
    """
    Deterministic world entity representation.
    """

    name: str
    entity_type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "System"
    confidence: float = 1.0
    entity_id: str = field(default_factory=lambda: f"ent-{uuid.uuid4().hex[:8]}")
    created_ts: float = field(default_factory=time.time)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "attributes": self.attributes,
            "provenance": self.provenance,
            "confidence": round(self.confidence, 3),
            "version": self.version,
        }


@dataclass
class Relationship:
    """
    Directional, versioned relationship between two entities.
    """

    source_entity_id: str
    target_entity_id: str
    relationship_type: RelationshipType
    attributes: Dict[str, Any] = field(default_factory=dict)
    provenance: str = "System"
    confidence: float = 1.0
    relationship_id: str = field(default_factory=lambda: f"rel-{uuid.uuid4().hex[:8]}")
    created_ts: float = field(default_factory=time.time)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "relationship_type": self.relationship_type.value,
            "attributes": self.attributes,
            "provenance": self.provenance,
            "confidence": round(self.confidence, 3),
            "version": self.version,
        }


@dataclass
class SemanticFact:
    """
    Immutable semantic fact with traceable provenance.
    """

    origin_subsystem: str
    source_entity_id: str
    relationship_type: RelationshipType
    target_entity_id: str
    supporting_evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    fact_id: str = field(default_factory=lambda: f"fct-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    validation_state: str = "VALIDATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "origin_subsystem": self.origin_subsystem,
            "source_entity_id": self.source_entity_id,
            "relationship_type": self.relationship_type.value,
            "target_entity_id": self.target_entity_id,
            "supporting_evidence": self.supporting_evidence,
            "confidence": round(self.confidence, 3),
            "timestamp_iso": self.timestamp_iso,
            "validation_state": self.validation_state,
        }
