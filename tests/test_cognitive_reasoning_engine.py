"""
Comprehensive Test Suite for MEMORA Phase 24 — Cognitive Reasoning Engine Framework.

Tests all Phase 24 modules:
1. Data Models & Serialization (Observation, Hypothesis, ConflictRecord, ReasoningGraphNode)
2. Cognitive Blackboard (Workspace storage, retrieval, TTL pruning)
3. Confidence Propagation Engine (Agreement rewards, contradiction penalties, temporal decay)
4. Temporal Reasoner (Qualitative relations & narratives)
5. Conflict Detector & Resolver (Location mismatches, goal/reminder conflicts)
6. Hypothesis Manager & State Estimator (Hypothesis lifecycle, state mode inference)
7. Explanation Builder & Reasoning Graph (Tree node generation & narrative)
8. Central Cognitive Reasoning Engine (Multi-modal reasoning, latency tracking)
9. Pipeline Reasoning Integration (CognitivePipeline step 6.7 & stream emission)
"""

import os
import tempfile
import time
import pytest

from src.reasoning.reasoning_models import (
    CognitiveStateMode,
    ConflictRecord,
    Hypothesis,
    HypothesisStatus,
    Observation,
    ObservationCategory,
    ReasoningGraphNode,
    ReasoningNodeType,
    TemporalRelation,
)
from src.reasoning.blackboard import CognitiveBlackboard
from src.reasoning.confidence_engine import ConfidenceEngine
from src.reasoning.temporal_reasoner import TemporalReasoner
from src.reasoning.conflict_detector import ConflictDetector
from src.reasoning.hypothesis_manager import HypothesisManager
from src.reasoning.explanation_builder import ExplanationBuilder
from src.reasoning.reasoning_engine import CognitiveReasoningEngine


# ======================================================================
# 1. Reasoning Models Tests
# ======================================================================

class TestReasoningModels:
    def test_observation_to_dict(self):
        obs = Observation(
            source="TestCamera",
            category=ObservationCategory.VISION_OBJECT,
            payload={"object_name": "reading glasses", "location": "Living Room"},
            confidence=0.90,
            importance=0.80,
        )
        d = obs.to_dict()
        assert d["source"] == "TestCamera"
        assert d["category"] == "VISION_OBJECT"
        assert d["confidence"] == 0.90
        assert obs.is_expired() is False

    def test_hypothesis_to_dict(self):
        hyp = Hypothesis(
            title="User searching for glasses",
            state_mode=CognitiveStateMode.SEARCHING,
            confidence=0.85,
            status=HypothesisStatus.ACTIVE,
        )
        d = hyp.to_dict()
        assert d["title"] == "User searching for glasses"
        assert d["state_mode"] == "SEARCHING"
        assert d["confidence"] == 0.85

    def test_conflict_record_to_dict(self):
        cnf = ConflictRecord(
            title="Location Mismatch",
            opposing_evidence_a="Vision: Living Room",
            opposing_evidence_b="Behaviour: Bedroom",
            resolution_strategy="Evidence Weighting",
            resolved_winner="Vision",
            explanation="Vision detected glasses in Living Room",
        )
        d = cnf.to_dict()
        assert d["resolved_winner"] == "Vision"
        assert d["title"] == "Location Mismatch"


# ======================================================================
# 2. Cognitive Blackboard Tests
# ======================================================================

class TestCognitiveBlackboard:
    def test_post_and_get_observations(self):
        bb = CognitiveBlackboard()
        obs = bb.post_observation(
            source="TestHAL",
            category=ObservationCategory.SENSOR_HAL,
            payload={"reading": 42},
            confidence=0.95,
        )
        assert obs.observation_id.startswith("obs-")
        active = bb.get_active_observations(category=ObservationCategory.SENSOR_HAL)
        assert len(active) == 1
        assert active[0].payload["reading"] == 42

    def test_ttl_pruning(self):
        bb = CognitiveBlackboard()
        bb.post_observation(
            source="TestHAL",
            category=ObservationCategory.SENSOR_HAL,
            payload={},
            expiry_seconds=0.001,
        )
        time.sleep(0.01)
        purged = bb.prune_expired()
        assert purged >= 1
        assert len(bb.get_active_observations()) == 0


# ======================================================================
# 3. Confidence Propagation Engine Tests
# ======================================================================

class TestConfidenceEngine:
    def test_apply_agreement_reward(self):
        boosted = ConfidenceEngine.apply_agreement_reward(0.50, 0.80)
        assert boosted > 0.50
        assert boosted <= 1.0

    def test_apply_contradiction_penalty(self):
        penalized = ConfidenceEngine.apply_contradiction_penalty(0.80, 0.90)
        assert penalized < 0.80
        assert penalized >= 0.0

    def test_apply_temporal_decay(self):
        decayed = ConfidenceEngine.apply_temporal_decay(0.80, age_seconds=300.0, half_life_sec=300.0)
        assert abs(decayed - 0.40) < 0.05

    def test_combine_evidence(self):
        supp = [Observation(source="S1", category=ObservationCategory.VISION_FACE, payload={}, confidence=0.90)]
        contra = [Observation(source="S2", category=ObservationCategory.VISION_FACE, payload={}, confidence=0.50)]
        score = ConfidenceEngine.combine_evidence(0.50, supp, contra)
        assert 0.05 <= score <= 0.95


# ======================================================================
# 4. Temporal Reasoner Tests
# ======================================================================

class TestTemporalReasoner:
    def test_evaluate_relation(self):
        obs = Observation(source="S1", category=ObservationCategory.VISION_FACE, payload={})
        rel = TemporalReasoner.evaluate_relation(obs)
        assert rel == TemporalRelation.STILL_OCCURRING

    def test_format_time_narrative(self):
        text = TemporalReasoner.format_time_narrative("reading glasses", "seen in Kitchen", 240.0)
        assert "reading glasses was seen in Kitchen 4 minutes ago." in text


# ======================================================================
# 5. Conflict Detector Tests
# ======================================================================

class TestConflictDetector:
    def test_detect_location_conflict(self):
        o1 = Observation(
            source="VisionPipeline",
            category=ObservationCategory.VISION_OBJECT,
            payload={"object_name": "reading glasses", "location": "Living Room"},
            confidence=0.90,
        )
        o2 = Observation(
            source="BehaviourEngine",
            category=ObservationCategory.BEHAVIOUR_PREDICTION,
            payload={"object_name": "reading glasses", "location": "Bedroom"},
            confidence=0.60,
        )
        conflicts = ConflictDetector.detect_conflicts([o1, o2])
        assert len(conflicts) == 1
        assert "Location Mismatch" in conflicts[0].title
        assert conflicts[0].resolved_winner == "VisionPipeline"

    def test_detect_goal_reminder_conflict(self):
        g_obs = Observation(
            source="GoalManager",
            category=ObservationCategory.GOAL_STATE,
            payload={"goal_name": "Morning Medication", "status": "SATISFIED"},
        )
        r_obs = Observation(
            source="ClinicalState",
            category=ObservationCategory.CLINICAL_STATE,
            payload={"reminder_name": "Morning Medication Prompt", "reminder_active": True},
        )
        conflicts = ConflictDetector.detect_conflicts([g_obs, r_obs])
        assert len(conflicts) == 1
        assert conflicts[0].resolved_winner == "Goal Engine"


# ======================================================================
# 6. Hypothesis Manager & Explanation Builder Tests
# ======================================================================

class TestHypothesisAndExplanation:
    def test_evaluate_hypotheses_searching(self):
        mgr = HypothesisManager()
        obs = Observation(
            source="SpeechEngine",
            category=ObservationCategory.SENSOR_HAL,
            payload={"transcript": "where are my reading glasses?"},
        )
        hyps, mode = mgr.evaluate_hypotheses([obs])
        assert mode == CognitiveStateMode.SEARCHING
        assert hyps[0].confidence >= 0.50

    def test_build_reasoning_graph(self):
        obs = Observation(source="S1", category=ObservationCategory.VISION_FACE, payload={})
        hyp = Hypothesis(title="User conversing", state_mode=CognitiveStateMode.CONVERSING, confidence=0.80)
        nodes, narrative = ExplanationBuilder.build_reasoning_graph(
            estimated_state=CognitiveStateMode.CONVERSING,
            top_hypothesis=hyp,
            supporting_observations=[obs],
        )
        assert len(nodes) >= 3
        assert "Conclusion: 'CONVERSING'" in narrative


# ======================================================================
# 7. Central Reasoning Engine Tests
# ======================================================================

class TestCognitiveReasoningEngine:
    def test_reasoning_cycle(self):
        engine = CognitiveReasoningEngine()
        summary = engine.reason(
            event_name="Sarah",
            location="Living Room",
            user_speech="where are my glasses?",
            patient_state_mode="Calm",
            active_goal_name="Morning Medication",
        )
        assert summary["cycle"] == 1
        assert "cognitive_state" in summary
        assert summary["reasoning_latency_ms"] >= 0.0

    def test_reset(self):
        engine = CognitiveReasoningEngine()
        engine.reason(event_name="Sarah", location="Living Room")
        engine.reset()
        assert len(engine.blackboard.get_active_observations()) == 0


# ======================================================================
# 8. Pipeline Integration Tests
# ======================================================================

class TestPipelineReasoningIntegration:
    def test_pipeline_instantiates_reasoning_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_reasoning_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "reasoning_engine")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.reasoning_engine._cycle_counter == 1
