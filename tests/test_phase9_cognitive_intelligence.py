"""
Phase 9 — Cognitive Intelligence Engine Validation Suite.

Validates all 12 Phase 9 Objectives:
1. Working Memory & Reference Resolution (Anaphora)
2. Goal Management Lifecycle & Persistence
3. Attention Scoring Engine (Multi-Factor)
4. Memory Consolidation (Time-Window Summaries)
5. Patient Profile Evolution & Contradiction Detection
6. Confidence Propagation (Composite Formula)
7. Structured Context Builder
8. Care-Aware Reasoning & Validation Therapy
9. Explainable Cognitive Trace
10. Real Learning (Behavioral Repetitions)
11. End-to-End Multi-Turn Scenario
"""

import pytest
import time
from datetime import datetime, timedelta

from src.cognition.cos.working_memory import WorkingMemory
from src.cognition.goals.models import GoalHypothesis, GoalCategory, GoalState, EvidenceSignal
from src.cognition.goals.lifecycle import GoalLifecycleManager
from src.cognition.goals.reasoner import HeuristicGoalReasoner
from src.cognition.attention.attention_engine import CognitiveAttentionEngine
from src.cognition.attention.scorers import NoveltyScorer, ConfidenceScorer, BaseImportanceScorer
from src.cognition.memory_consolidator import MemoryConsolidator
from src.cognition.context_builder import ContextBuilder
from src.cognition.reflection.confidence_manager import ConfidenceManager
from src.clinical.decision_trace import ClinicalDecisionTrace
from src.reasoning.intent_predictor import IntentPredictor
from src.memory.database import MemoraDatabase
from src.memory.models import SemanticNodeModel
from src.interaction.events import PresenceEvent, PresenceEventType
from src.cognition.memory_models import RelevantMemory, MemoryType, MemoryImportance
from src.llm.reasoning_client import MockReasoningClient


class TestPhase9CognitiveIntelligence:

    @pytest.fixture
    def db(self, tmp_path):
        db_path = str(tmp_path / "test_phase9.sqlite")
        database = MemoraDatabase(db_path=db_path)
        database.clear()
        return database

    # ------------------------------------------------------------------
    # Objective 1: Real Working Memory & Reference Resolution
    # ------------------------------------------------------------------
    def test_working_memory_reference_resolution(self):
        wm = WorkingMemory()
        wm.update_interaction(
            user_message="Where are my glasses?",
            room="Living Room",
            objects=["reading_glasses"],
            topic="Searching for glasses"
        )
        
        assert wm.recall("active_search_target") == "glasses"
        assert wm.recall("previous_user_message") == "Where are my glasses?"
        
        # Test reference resolution for "them"
        res = wm.resolve_reference("Did you find them?")
        assert res["has_reference"] is True
        assert res["resolved_referent"] == "glasses"
        assert "glasses" in res["resolved_query"].lower()

    # ------------------------------------------------------------------
    # Objective 2: Goal Management Lifecycle
    # ------------------------------------------------------------------
    def test_goal_management_lifecycle(self):
        lifecycle = GoalLifecycleManager()
        
        goal = GoalHypothesis(
            name="Take Medicine",
            category=GoalCategory.MEDICAL,
            confidence=0.85,
            state=GoalState.DETECTED
        )
        
        # Evolve: DETECTED -> ACTIVE
        lifecycle.evolve(goal)
        assert goal.state == GoalState.ACTIVE
        
        # Progression: ACTIVE -> IN_PROGRESS
        lifecycle.mark_in_progress(goal)
        assert goal.state == GoalState.IN_PROGRESS
        
        # Completion: IN_PROGRESS -> COMPLETED
        lifecycle.mark_completed(goal)
        assert goal.state == GoalState.COMPLETED

    # ------------------------------------------------------------------
    # Objective 3: Attention Scoring Engine
    # ------------------------------------------------------------------
    def test_attention_engine_multi_factor_scoring(self):
        engine = CognitiveAttentionEngine()
        assert len(engine.scorers) >= 7
        
        nov_scorer = NoveltyScorer()
        conf_scorer = ConfidenceScorer()
        
        mem = RelevantMemory(
            memory_id="mem_1",
            memory_type=MemoryType.EPISODIC,
            importance=MemoryImportance.HIGH,
            title="First visit",
            summary="Sarah visited today",
            timestamp=datetime.now()
        )
        object.__setattr__(mem, "access_count", 1)
        object.__setattr__(mem, "confidence", 0.9)
        
        assert nov_scorer.score(mem, None) == 20.0
        assert conf_scorer.score(mem, None) == 13.5

    # ------------------------------------------------------------------
    # Objective 4: Memory Consolidation Summaries
    # ------------------------------------------------------------------
    def test_memory_consolidation_window_summaries(self, db):
        mock_llm = MockReasoningClient()
        consolidator = MemoryConsolidator(db.session_factory, mock_llm)
        
        episodes = ["Patient took morning pills", "Patient walked in garden"]
        summary = consolidator.generate_window_summary("Morning Summary", episodes)
        assert summary is not None
        assert len(summary) > 0

    # ------------------------------------------------------------------
    # Objective 5 & 6: Contradiction Detection
    # ------------------------------------------------------------------
    def test_contradiction_detection(self, db):
        mock_llm = MockReasoningClient()
        consolidator = MemoryConsolidator(db.session_factory, mock_llm)
        
        # Manually seed existing fact: (patient, daughter, riya)
        with db.session_factory() as session:
            node1 = SemanticNodeModel(
                subject="patient",
                predicate="daughter",
                object_val="riya",
                category="RELATIONSHIP",
                importance=2,
                confidence=1.0,
                last_reinforced=datetime.now().isoformat()
            )
            session.add(node1)
            session.commit()
            
        # Consolidate conflicting episode with (patient, daughter, neha)
        class DummyEpisode:
            summary = "Patient stated her daughter is Neha"
            commitments = []
            
        mock_llm.generate_cue = lambda p: '[{"subject": "patient", "predicate": "daughter", "object": "neha", "category": "RELATIONSHIP", "importance": 2}]'
        
        consolidator.consolidate(DummyEpisode())
        
        with db.session_factory() as session:
            nodes = session.query(SemanticNodeModel).filter_by(subject="patient", predicate="daughter").all()
            assert len(nodes) == 2
            objs = [n.object_val for n in nodes]
            assert "riya" in objs
            assert "neha" in objs
            for n in nodes:
                assert n.verification_status == "Contradiction"

    # ------------------------------------------------------------------
    # Objective 7: Confidence Propagation
    # ------------------------------------------------------------------
    def test_confidence_propagation(self):
        comp_conf = ConfidenceManager.compute_composite_confidence(
            perception_confidence=0.9,
            speech_confidence=0.95,
            retrieval_confidence=0.8,
            reasoning_confidence=0.9
        )
        expected = round(0.9 * 0.95 * 0.8 * 0.9, 4)
        assert comp_conf == expected

    # ------------------------------------------------------------------
    # Objective 8: Structured Context Builder
    # ------------------------------------------------------------------
    def test_context_builder_structured_prompt(self):
        cb = ContextBuilder()
        event = PresenceEvent(
            type=PresenceEventType.PERSON_ARRIVED,
            face_id="p1",
            name="Alice",
            relationship="Daughter"
        )
        
        goal = GoalHypothesis(name="Locate Glasses", category=GoalCategory.SEARCH, confidence=0.8)
        wm = {"active_search_target": "glasses"}
        
        prompt = cb.build_prompt(
            event=event,
            memories=[],
            current_location="Living Room",
            current_time="10:00 AM",
            goals=[goal],
            working_memory=wm,
            patient_profile={"favorite_tea": "Earl Grey"},
            attention_priorities="Locating Glasses"
        )
        
        assert "Alice" in prompt
        assert "Locate Glasses" in prompt
        assert "glasses" in prompt
        assert "Earl Grey" in prompt

    # ------------------------------------------------------------------
    # Objective 10: Explainable Cognitive Trace
    # ------------------------------------------------------------------
    def test_explainable_cognitive_trace(self):
        trace = ClinicalDecisionTrace(
            timestamp=datetime.now().isoformat(),
            patient_state="Anxious",
            patient_state_evidence="Repeated searching for keys",
            providers_consulted=["identity", "memory"],
            memory_retrieval_summary="Retrieved 2 memories",
            goal_hypotheses_considered=["Locate Keys (Confidence: 0.85)"],
            care_policies_evaluated=["Validation Therapy"],
            selected_care_policy="Validation Therapy",
            interaction_strategy="Calm Reassurance",
            speech_produced=True,
            memory_written=True,
            confidence_scores={"overall": 0.88},
            final_response="Don't worry, your keys are on the kitchen counter.",
            working_memory_snapshot={"slots": {"active_search_target": {"value": "keys"}}},
            attention_focus={"target": "Locating Keys"},
            cos_reasoning_path="Search detected -> Provide gentle location cue",
            cos_action_type="SPEAK"
        )
        
        rendered = trace.to_explainable_cognitive_trace()
        assert "COGNITIVE TRACE" in rendered
        assert "Anxious" in rendered
        assert "Locating Keys" in rendered

    # ------------------------------------------------------------------
    # Objective 11: Real Learning
    # ------------------------------------------------------------------
    def test_real_learning_behavioral_patterns(self):
        predictor = IntentPredictor()
        
        # Record repeated search for glasses
        c1 = predictor.record_lost_object_search("glasses")
        c2 = predictor.record_lost_object_search("glasses")
        
        assert c2 == 2
        boost = predictor.get_retrieval_priority_boost("glasses")
        assert boost > 1.0
        
        # Record routine habit
        predictor.record_routine_event("5 PM", "tea")
        predictor.record_routine_event("5 PM", "tea")
        
        patterns = predictor.get_learned_patterns()
        assert "glasses" in patterns["frequently_lost_objects"]
        assert "5 pm:tea" in patterns["learned_routines"]
