"""
MEMORA Relationship Registry.

Provides thread-safe registration, lookup, and query indexing for directional relationships across 10 relationship types:
BELONGS_TO, LOCATED_IN, CONNECTED_TO, REQUIRES, CONTAINS, PART_OF, SCHEDULED_BEFORE, SCHEDULED_AFTER, MANAGED_BY, INTERACTS_WITH
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.knowledge.knowledge_models import Relationship, RelationshipType


class RelationshipRegistry:
    """
    Thread-safe registry for directional entity relationships.
    """

    def __init__(self) -> None:
        self._relationships: Dict[str, Relationship] = {}
        self._outgoing_index: Dict[str, List[str]] = {}
        self._incoming_index: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
        self._seed_baseline_relationships()

    def register_relationship(self, relationship: Relationship) -> Relationship:
        with self._lock:
            rid = relationship.relationship_id
            self._relationships[rid] = relationship

            src = relationship.source_entity_id
            tgt = relationship.target_entity_id

            if src not in self._outgoing_index:
                self._outgoing_index[src] = []
            self._outgoing_index[src].append(rid)

            if tgt not in self._incoming_index:
                self._incoming_index[tgt] = []
            self._incoming_index[tgt].append(rid)

            return relationship

    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        with self._lock:
            return self._relationships.get(relationship_id)

    def get_outgoing_relationships(self, entity_id: str) -> List[Relationship]:
        with self._lock:
            rids = self._outgoing_index.get(entity_id, [])
            return [self._relationships[rid] for rid in rids if rid in self._relationships]

    def get_incoming_relationships(self, entity_id: str) -> List[Relationship]:
        with self._lock:
            rids = self._incoming_index.get(entity_id, [])
            return [self._relationships[rid] for rid in rids if rid in self._relationships]

    def get_all_relationships(self) -> List[Relationship]:
        with self._lock:
            return list(self._relationships.values())

    def clear(self) -> None:
        with self._lock:
            self._relationships.clear()
            self._outgoing_index.clear()
            self._incoming_index.clear()

    def _seed_baseline_relationships(self) -> None:
        """Seed baseline directional relationships."""
        r1 = Relationship(relationship_id="rel-glasses-loc", source_entity_id="ent-glasses", target_entity_id="ent-living-room", relationship_type=RelationshipType.LOCATED_IN)
        r2 = Relationship(relationship_id="rel-glasses-owner", source_entity_id="ent-glasses", target_entity_id="ent-margaret", relationship_type=RelationshipType.BELONGS_TO)
        r3 = Relationship(relationship_id="rel-med-owner", source_entity_id="ent-donepezil", target_entity_id="ent-margaret", relationship_type=RelationshipType.BELONGS_TO)
        r4 = Relationship(relationship_id="rel-room-conn1", source_entity_id="ent-living-room", target_entity_id="ent-kitchen", relationship_type=RelationshipType.CONNECTED_TO)
        r5 = Relationship(relationship_id="rel-room-conn2", source_entity_id="ent-living-room", target_entity_id="ent-dining-room", relationship_type=RelationshipType.CONNECTED_TO)
        r6 = Relationship(relationship_id="rel-room-conn3", source_entity_id="ent-bedroom", target_entity_id="ent-living-room", relationship_type=RelationshipType.CONNECTED_TO)
        r7 = Relationship(relationship_id="rel-sarah-caregiver", source_entity_id="ent-sarah", target_entity_id="ent-margaret", relationship_type=RelationshipType.INTERACTS_WITH)

        for r in [r1, r2, r3, r4, r5, r6, r7]:
            rid = r.relationship_id
            self._relationships[rid] = r
            self._outgoing_index.setdefault(r.source_entity_id, []).append(rid)
            self._incoming_index.setdefault(r.target_entity_id, []).append(rid)
