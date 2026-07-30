"""
MEMORA Central Knowledge Engine.

Orchestrates EntityRegistry, RelationshipRegistry, KnowledgeGraph, OntologyManager,
FactRepository, KnowledgeQueryEngine, GraphTraverser, SemanticValidator, and TemporalKnowledgeManager.

Positioned as a dedicated semantic knowledge subsystem between Experience Learning (Phase 26)
and Cognitive Reasoning Engine (Phase 24). Inherits from ICognitiveSubsystem.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.knowledge.knowledge_models import Entity, EntityType, Relationship, RelationshipType, SemanticFact
from src.knowledge.entity_registry import EntityRegistry
from src.knowledge.relationship_registry import RelationshipRegistry
from src.knowledge.knowledge_graph import KnowledgeGraph
from src.knowledge.ontology_manager import OntologyManager
from src.knowledge.fact_repository import FactRepository
from src.knowledge.knowledge_query_engine import KnowledgeQueryEngine
from src.knowledge.graph_traverser import GraphTraverser
from src.knowledge.semantic_validator import SemanticValidator
from src.knowledge.temporal_knowledge import TemporalKnowledgeManager
from src.knowledge.knowledge_explainer import KnowledgeExplainer


class KnowledgeEngine(ICognitiveSubsystem):
    """
    Central Knowledge Subsystem Orchestrator.
    """

    def __init__(self) -> None:
        self.entity_registry = EntityRegistry()
        self.relationship_registry = RelationshipRegistry()
        self.graph = KnowledgeGraph(self.entity_registry, self.relationship_registry)
        self.ontology_manager = OntologyManager()
        self.fact_repository = FactRepository()
        self.query_engine = KnowledgeQueryEngine(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.temporal_manager = TemporalKnowledgeManager()
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.RLock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_cycle(
            location=input_data.get("location", "Living Room"),
            active_person=input_data.get("active_person"),
        )

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            val = SemanticValidator.validate_graph(self.graph)
            return {
                "status": self._status,
                "is_graph_valid": val["is_valid"],
                "total_entities": len(self.entity_registry.get_all_entities()),
                "total_relationships": len(self.relationship_registry.get_all_relationships()),
            }

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {"cycle_count": self._cycle_counter}

    def explain(self) -> str:
        objs = self.query_engine.find_objects_in_room("Living Room")
        if objs:
            return f"Knowledge Engine: Living Room contains '{objs[0].name}'."
        return "Knowledge Engine: World model active with 8 baseline entities."

    def process_cycle(
        self,
        location: str = "Living Room",
        active_person: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute one cycle of semantic knowledge validation and query synthesis.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Query objects in current room
        room_objs = self.query_engine.find_objects_in_room(location)

        # 2. Query patient medications
        patient_meds = self.query_engine.find_medications_for_patient("Margaret")

        # 3. Perform shortest path traversal from Reading Glasses to Margaret
        path_nodes, path_steps = self.traverser.find_shortest_path("ent-glasses", "ent-margaret")

        # 4. Validate graph integrity
        val_report = SemanticValidator.validate_graph(self.graph)

        narrative = KnowledgeExplainer.generate_query_explanation(
            query_type=f"Room '{location}' Objects & Patient Medications",
            results=room_objs + patient_meds,
            explanation_steps=path_steps,
        )

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "entities_count": len(self.entity_registry.get_all_entities()),
            "relationships_count": len(self.relationship_registry.get_all_relationships()),
            "facts_count": len(self.fact_repository.get_all_facts()),
            "room_objects": [e.to_dict() for e in room_objs],
            "patient_medications": [m.to_dict() for m in patient_meds],
            "graph_validation": val_report,
            "explanation_narrative": narrative,
            "knowledge_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.entity_registry.clear()
            self.relationship_registry.clear()
            self.fact_repository.clear()
            self.entity_registry._seed_baseline_entities()
            self.relationship_registry._seed_baseline_relationships()
            self.fact_repository._seed_baseline_facts()
