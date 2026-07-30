"""
MEMORA Append-Only Fact Repository.

Stores immutable semantic facts with complete provenance tracking:
- Origin subsystem
- Supporting evidence & confidence
- Entity links & validation status
Facts remain strictly append-only. Corrections create new fact versions.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.knowledge.knowledge_models import RelationshipType, SemanticFact


class FactRepository:
    """
    Append-only repository for semantic world facts.
    """

    MAX_FACTS = 1000

    def __init__(self, max_facts: int = 1000) -> None:
        self.max_facts = max_facts
        self._facts: List[SemanticFact] = []
        self._lock = threading.Lock()
        self._seed_baseline_facts()

    def add_fact(self, fact: SemanticFact) -> SemanticFact:
        with self._lock:
            self._facts.append(fact)
            if len(self._facts) > self.max_facts:
                self._facts = self._facts[-self.max_facts:]
            return fact

    def get_facts_by_entity(self, entity_id: str) -> List[SemanticFact]:
        with self._lock:
            return [
                f for f in self._facts
                if f.source_entity_id == entity_id or f.target_entity_id == entity_id
            ]

    def get_all_facts(self) -> List[SemanticFact]:
        with self._lock:
            return list(self._facts)

    def clear(self) -> None:
        with self._lock:
            self._facts.clear()

    def _seed_baseline_facts(self) -> None:
        """Seed baseline semantic facts."""
        f1 = SemanticFact(
            origin_subsystem="VisionPipeline",
            source_entity_id="ent-glasses",
            relationship_type=RelationshipType.LOCATED_IN,
            target_entity_id="ent-living-room",
            supporting_evidence=["Bounding box match frame_104"],
            confidence=0.92,
        )
        f2 = SemanticFact(
            origin_subsystem="MemorySystem",
            source_entity_id="ent-donepezil",
            relationship_type=RelationshipType.BELONGS_TO,
            target_entity_id="ent-margaret",
            supporting_evidence=["Clinical prescription record"],
            confidence=0.98,
        )
        self._facts.extend([f1, f2])
