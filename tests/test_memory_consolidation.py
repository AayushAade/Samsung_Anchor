"""
Comprehensive Test Suite for MEMORA Phase 29 — Long-Term Memory Consolidation & Cognitive Recall Framework.

Tests all Phase 29 modules:
1. Data Models & Serialization (MemoryRecord, ReconstructedContext)
2. Memory Repository (Active & archived storage, archiving, restoration)
3. Memory Encoder (Observation, experience, knowledge fact encoding)
4. Memory Consolidator (Deduplication, importance weight updating, versioning)
5. Synchronized Multi-Index Registry (Entity, category, importance queries)
6. Cognitive Memory Recall Engine (Deterministic keyword recall & explanations)
7. Context Reconstructor & Associative Memory Engine (Context reconstruction & associative network)
8. Retention & Forgetting Managers (Expiration rules, audit-trailed archiving, recoverability)
9. Memory Validator & Explainer (Repository integrity validation & narrative generation)
10. Central Memory Engine (Multi-cycle processing, latency tracking, ICognitiveSubsystem compliance)
11. Pipeline Memory Integration (CognitivePipeline step 6.55 & stream emission)
"""

import os
import tempfile
import time
import pytest

from src.memory.memory_models import (
    MemoryCategory,
    MemoryRecord,
    ReconstructedContext,
    RetentionPolicy,
)
from src.memory.memory_repository import MemoryRepository
from src.memory.memory_encoder import MemoryEncoder
from src.memory.memory_consolidator import MemoryConsolidator
from src.memory.memory_index import MemoryIndex
from src.memory.memory_recall_engine import MemoryRecallEngine
from src.memory.context_reconstructor import ContextReconstructor
from src.memory.associative_memory import AssociativeMemoryEngine
from src.memory.retention_manager import RetentionManager
from src.memory.forgetting_manager import ForgettingManager
from src.memory.memory_validator import MemoryValidator
from src.memory.memory_explainer import MemoryExplainer
from src.memory.memory_engine import MemoryEngine


# ======================================================================
# 1. Memory Models Tests
# ======================================================================

class TestMemoryModels:
    def test_memory_record_to_dict(self):
        rec = MemoryRecord(content="Glasses on coffee table", category=MemoryCategory.OBSERVATION)
        d = rec.to_dict()
        assert d["content"] == "Glasses on coffee table"
        assert d["category"] == "OBSERVATION"
        assert d["is_archived"] is False

    def test_reconstructed_context_to_dict(self):
        rc = ReconstructedContext(
            memory_id="mem-1",
            surrounding_events=["Event A"],
            knowledge_facts=["Fact A"],
            executive_decisions=["Decision A"],
            explanation="Reconstructed",
        )
        d = rc.to_dict()
        assert d["memory_id"] == "mem-1"


# ======================================================================
# 2. Memory Repository Tests
# ======================================================================

class TestMemoryRepository:
    def test_repository_active_and_archive(self):
        repo = MemoryRepository()
        rec = MemoryRecord(content="Test Memory", category=MemoryCategory.OBSERVATION)
        repo.add_record(rec)
        assert len(repo.get_all_active()) >= 3  # Includes baseline records

        archived = repo.archive_record(rec.memory_id)
        assert archived is not None
        assert archived.is_archived is True

        restored = repo.restore_record(rec.memory_id)
        assert restored is not None
        assert restored.is_archived is False


# ======================================================================
# 3. Memory Encoder Tests
# ======================================================================

class TestMemoryEncoder:
    def test_encode_methods(self):
        obs = MemoryEncoder.encode_observation("User arrived")
        assert obs.category == MemoryCategory.OBSERVATION

        exp = MemoryEncoder.encode_experience("Found glasses successfully")
        assert exp.category == MemoryCategory.EXPERIENCE

        fact = MemoryEncoder.encode_knowledge_fact("Medication scheduled 08:30")
        assert fact.category == MemoryCategory.KNOWLEDGE_FACT


# ======================================================================
# 4. Memory Consolidator Tests
# ======================================================================

class TestMemoryConsolidator:
    def test_consolidate_duplicate(self):
        repo = MemoryRepository()
        consolidator = MemoryConsolidator(repo)
        rec1 = MemoryRecord(content="Duplicate Content", category=MemoryCategory.OBSERVATION, importance=0.50)
        consolidator.consolidate_new_record(rec1)

        rec2 = MemoryRecord(content="Duplicate Content", category=MemoryCategory.OBSERVATION, importance=0.70)
        merged, is_dup = consolidator.consolidate_new_record(rec2)
        assert is_dup is True
        assert merged.importance >= 0.70
        assert merged.version == 2


# ======================================================================
# 5. Multi-Index Registry Tests
# ======================================================================

class TestMemoryIndex:
    def test_query_by_entity(self):
        repo = MemoryRepository()
        idx = MemoryIndex(repo)
        results = idx.query_by_entity("Margaret")
        assert len(results) >= 1

    def test_query_by_category(self):
        repo = MemoryRepository()
        idx = MemoryIndex(repo)
        results = idx.query_by_category(MemoryCategory.KNOWLEDGE_FACT)
        assert len(results) >= 1


# ======================================================================
# 6. Memory Recall Engine Tests
# ======================================================================

class TestMemoryRecallEngine:
    def test_recall_by_keyword(self):
        repo = MemoryRepository()
        idx = MemoryIndex(repo)
        mre = MemoryRecallEngine(repo, idx)
        results, explanation = mre.recall_by_keyword("Glasses")
        assert len(results) >= 1
        assert "Deterministic Recall" in explanation


# ======================================================================
# 7. Context Reconstructor & Associative Memory Tests
# ======================================================================

class TestContextAndAssociative:
    def test_context_reconstructor(self):
        repo = MemoryRepository()
        cr = ContextReconstructor(repo)
        rec = repo.get_all_active()[0]
        ctx = cr.reconstruct_context(rec)
        assert ctx.memory_id == rec.memory_id

    def test_associative_memory(self):
        ame = AssociativeMemoryEngine()
        concepts = ame.get_associated_concepts("reading glasses")
        assert "margaret" in concepts or "living room" in concepts


# ======================================================================
# 8. Retention & Forgetting Managers Tests
# ======================================================================

class TestRetentionAndForgetting:
    def test_retention_evaluation(self):
        rec_clinical = MemoryRecord(content="Clinical", category=MemoryCategory.KNOWLEDGE_FACT, retention_policy=RetentionPolicy.CLINICAL)
        assert RetentionManager.is_expired(rec_clinical) is False

    def test_forgetting_manager(self):
        repo = MemoryRepository()
        fm = ForgettingManager(repo)
        archived, audit = fm.evaluate_and_archive_expired()
        assert isinstance(archived, list)


# ======================================================================
# 9. Memory Validator & Explainer Tests
# ======================================================================

class TestValidatorAndExplainer:
    def test_memory_validator(self):
        repo = MemoryRepository()
        val = MemoryValidator.validate_repository(repo)
        assert val["is_valid"] is True

    def test_memory_explainer(self):
        repo = MemoryRepository()
        rec = repo.get_all_active()[0]
        exp = MemoryExplainer.generate_recall_explanation("Keyword", [rec], "Recall Rationale")
        assert "Long-Term Memory Recall Explanation" in exp


# ======================================================================
# 10. Central Memory Engine Tests
# ======================================================================

class TestMemoryEngine:
    def test_process_cycle(self):
        me = MemoryEngine()
        summary = me.process_cycle(user_speech="Where are my glasses?", location="Living Room")
        assert summary["cycle"] == 1
        assert summary["active_memories_count"] >= 3
        assert summary["memory_latency_ms"] >= 0.0

    def test_reset(self):
        me = MemoryEngine()
        me.process_cycle(location="Living Room")
        me.reset()
        assert me._cycle_counter == 0


# ======================================================================
# 11. Pipeline Memory Integration Tests
# ======================================================================

class TestPipelineMemoryIntegration:
    def test_pipeline_instantiates_memory_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_memory_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "ltm_memory_engine") or hasattr(pipeline, "memory_engine")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        engine = getattr(pipeline, "ltm_memory_engine", getattr(pipeline, "memory_engine", None))
        assert engine._cycle_counter == 1
