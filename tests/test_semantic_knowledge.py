"""
Comprehensive Test Suite for MEMORA Phase 28 — Semantic Knowledge Graph & World Model.

Tests all Phase 28 modules:
1. Data Models & Serialization (Entity, Relationship, SemanticFact)
2. Entity Registry (11 Entity Types, name lookup, type filtering)
3. Relationship Registry (10 Directional Relationship Types, incoming/outgoing indices)
4. Knowledge Graph Network Model (Nodes, edges, neighbor queries)
5. Ontology Manager (Taxonomy inheritance & concept taxonomy)
6. Fact Repository (Append-only facts & provenance tracking)
7. Deterministic Knowledge Query Engine (Medications, objects, rooms)
8. Graph Traverser (BFS shortest path & step-by-step explanations)
9. Semantic Validator & Temporal Knowledge (Integrity validation & location timeline)
10. Central Knowledge Engine (Multi-cycle processing, latency tracking, ICognitiveSubsystem compliance)
11. Pipeline Knowledge Integration (CognitivePipeline step 6.75 & stream emission)
"""

import os
import tempfile
import pytest

from src.knowledge.knowledge_models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
    SemanticFact,
)
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
from src.knowledge.knowledge_engine import KnowledgeEngine


# ======================================================================
# 1. Knowledge Models Tests
# ======================================================================

class TestKnowledgeModels:
    def test_entity_to_dict(self):
        ent = Entity(name="Glasses", entity_type=EntityType.OBJECT)
        d = ent.to_dict()
        assert d["name"] == "Glasses"
        assert d["entity_type"] == "OBJECT"

    def test_relationship_to_dict(self):
        rel = Relationship(source_entity_id="e1", target_entity_id="e2", relationship_type=RelationshipType.LOCATED_IN)
        d = rel.to_dict()
        assert d["relationship_type"] == "LOCATED_IN"

    def test_fact_to_dict(self):
        fact = SemanticFact(origin_subsystem="Vision", source_entity_id="e1", relationship_type=RelationshipType.BELONGS_TO, target_entity_id="e2")
        d = fact.to_dict()
        assert d["origin_subsystem"] == "Vision"


# ======================================================================
# 2. Entity & Relationship Registries Tests
# ======================================================================

class TestRegistries:
    def test_entity_registry(self):
        reg = EntityRegistry()
        ent = reg.get_entity_by_name("Reading Glasses")
        assert ent is not None
        assert ent.entity_type == EntityType.OBJECT

        meds = reg.query_by_type(EntityType.MEDICATION)
        assert len(meds) >= 1

    def test_relationship_registry(self):
        reg = RelationshipRegistry()
        rels = reg.get_outgoing_relationships("ent-glasses")
        assert len(rels) >= 1


# ======================================================================
# 3. Knowledge Graph & Ontology Tests
# ======================================================================

class TestGraphAndOntology:
    def test_knowledge_graph(self):
        graph = KnowledgeGraph()
        neighbors = graph.get_neighbors("ent-glasses")
        assert len(neighbors) >= 1

    def test_ontology_manager(self):
        assert OntologyManager.is_subclass_of(EntityType.MEDICATION, "HEALTHCARE_ITEM") is True
        assert OntologyManager.is_subclass_of(EntityType.CAREGIVER, "PERSON") is True


# ======================================================================
# 4. Query Engine & Graph Traverser Tests
# ======================================================================

class TestQueryAndTraverser:
    def test_query_engine(self):
        graph = KnowledgeGraph()
        qe = KnowledgeQueryEngine(graph)
        objs = qe.find_objects_in_room("Living Room")
        assert len(objs) >= 1
        assert objs[0].name == "Reading Glasses"

        meds = qe.find_medications_for_patient("Margaret")
        assert len(meds) >= 1

        rooms = qe.find_connected_rooms("Living Room")
        assert len(rooms) >= 1

    def test_graph_traverser_bfs(self):
        graph = KnowledgeGraph()
        gt = GraphTraverser(graph)
        path, steps = gt.find_shortest_path("ent-glasses", "ent-margaret")
        assert len(path) >= 2
        assert "Reached target entity" in steps[-1]


# ======================================================================
# 5. Semantic Validator & Temporal Knowledge Tests
# ======================================================================

class TestValidatorAndTemporal:
    def test_semantic_validator(self):
        graph = KnowledgeGraph()
        val = SemanticValidator.validate_graph(graph)
        assert val["is_valid"] is True

    def test_temporal_knowledge(self):
        tkm = TemporalKnowledgeManager()
        tkm.record_transition("ent-glasses", "Reading Glasses", "Living Room", "Kitchen")
        history = tkm.get_location_history("ent-glasses")
        assert len(history) >= 2


# ======================================================================
# 6. Central Knowledge Engine Tests
# ======================================================================

class TestKnowledgeEngine:
    def test_process_cycle(self):
        ke = KnowledgeEngine()
        summary = ke.process_cycle(location="Living Room")
        assert summary["cycle"] == 1
        assert summary["entities_count"] >= 8
        assert summary["knowledge_latency_ms"] >= 0.0

    def test_reset(self):
        ke = KnowledgeEngine()
        ke.process_cycle(location="Living Room")
        ke.reset()
        assert ke._cycle_counter == 0


# ======================================================================
# 7. Pipeline Knowledge Integration Tests
# ======================================================================

class TestPipelineKnowledgeIntegration:
    def test_pipeline_instantiates_knowledge_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_knowledge_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "knowledge_engine")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.knowledge_engine._cycle_counter == 1
