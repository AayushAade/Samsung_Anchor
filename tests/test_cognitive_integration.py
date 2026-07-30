"""
Repository-Wide Cross-Subsystem Integration Test Suite for MEMORA Phase 27.

Tests:
1. ICognitiveSubsystem Lifecycle (initialize, shutdown, process, status, health, metrics, explain)
2. UnifiedEvent & SharedDataContracts serialization
3. Cognitive Health Monitor Aggregator
4. Automated Dependency Graph Validator (Zero circular imports)
5. Multi-Layer Performance Benchmark Suite
6. End-to-End Cross-Subsystem Pipeline Integration (COS -> Trust -> Behaviour -> Reasoning -> Executive -> Experience -> Stream)
"""

import os
import tempfile
import pytest

from src.core.interfaces import ICognitiveSubsystem
from src.core.events import UnifiedEvent
from src.core.contracts import SharedContext, SharedDecision
from src.operations.cognitive_health import CognitiveHealthMonitor
from src.reasoning.reasoning_engine import CognitiveReasoningEngine
from src.executive.executive_engine import ExecutiveEngine
from src.experience.experience_engine import ExperienceEngine
from src.behaviour.behaviour_manager import BehaviourManager
from deployment.validation.dependency_validator import DependencyValidator
from deployment.benchmarks.benchmark_suite import BenchmarkSuite


# ======================================================================
# 1. ICognitiveSubsystem Lifecycle Tests
# ======================================================================

class TestICognitiveSubsystem:
    def test_reasoning_engine_lifecycle(self):
        engine = CognitiveReasoningEngine()
        assert isinstance(engine, ICognitiveSubsystem)
        assert engine.initialize() is True
        assert engine.status() == "RUNNING"
        
        output = engine.process({"event_name": "Sarah", "location": "Living Room"})
        assert "cognitive_state" in output
        assert engine.health()["status"] == "RUNNING"
        assert engine.metrics()["cycle_count"] == 1
        assert "Reasoning Engine" in engine.explain()
        assert engine.shutdown() is True

    def test_executive_engine_lifecycle(self):
        engine = ExecutiveEngine()
        assert isinstance(engine, ICognitiveSubsystem)
        assert engine.initialize() is True
        assert engine.status() == "RUNNING"

        output = engine.process({"location": "Living Room"})
        assert "top_goal" in output
        assert "Executive Engine" in engine.explain()
        assert engine.shutdown() is True

    def test_experience_engine_lifecycle(self):
        engine = ExperienceEngine()
        assert isinstance(engine, ICognitiveSubsystem)
        assert engine.initialize() is True

        output = engine.process({"location": "Living Room"})
        assert "total_records_count" in output
        assert "Experience Subsystem" in engine.explain()
        assert engine.shutdown() is True

    def test_behaviour_manager_lifecycle(self):
        manager = BehaviourManager()
        assert isinstance(manager, ICognitiveSubsystem)
        assert manager.initialize() is True

        output = manager.process({"event_name": "Sarah", "location": "Living Room"})
        assert "current_activity" in output
        assert "Behaviour Platform" in manager.explain()
        assert manager.shutdown() is True


# ======================================================================
# 2. Unified Events & Shared Data Contracts Tests
# ======================================================================

class TestUnifiedEventsAndContracts:
    def test_unified_event_serialization(self):
        evt = UnifiedEvent(
            origin="ReasoningEngine",
            destination="ExecutiveEngine",
            priority=0.85,
            confidence=0.90,
            payload={"cognitive_state": "SEARCHING"},
        )
        d = evt.to_dict()
        assert d["origin"] == "ReasoningEngine"
        assert d["destination"] == "ExecutiveEngine"
        assert d["version"] == "1.0.0"

    def test_shared_decision_serialization(self):
        sd = SharedDecision(
            subsystem="SafetyManager",
            decision_type="ALLOW",
            confidence=0.95,
            rationale="Passed all guardrails",
            action_message="Provide gentle prompt",
        )
        d = sd.to_dict()
        assert d["subsystem"] == "SafetyManager"
        assert d["decision_type"] == "ALLOW"


# ======================================================================
# 3. Cognitive Health & Dependency Validation Tests
# ======================================================================

class TestHealthAndDependencyValidation:
    def test_cognitive_health_monitor(self):
        chm = CognitiveHealthMonitor()
        chm.record_subsystem_health("CognitiveReasoning", "RUNNING", latency_ms=1.2)
        summary = chm.get_health_summary()
        assert summary["overall_status"] == "HEALTHY"
        assert summary["active_subsystems_count"] == 6

    def test_dependency_validator_no_circular_imports(self):
        is_valid, errors = DependencyValidator.validate_imports()
        assert is_valid is True
        assert len(errors) == 0

    def test_benchmark_suite(self):
        results = BenchmarkSuite.run_benchmarks(cycles=2)
        assert results["cycles_simulated"] == 2
        assert results["average_pipeline_latency_ms"] >= 0.0


# ======================================================================
# 4. End-to-End Integration Test
# ======================================================================

class TestEndToEndPipelineIntegration:
    def test_full_pipeline_cross_subsystem_flow(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db_path = os.path.join(tempfile.gettempdir(), "test_integration_pipeline.sqlite")
        db = MemoraDatabase(db_path=db_path)
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        # Verify presence of all subsystem engines
        assert hasattr(pipeline, "cognitive_kernel")
        assert hasattr(pipeline, "safety_manager")
        assert hasattr(pipeline, "behaviour_manager")
        assert hasattr(pipeline, "reasoning_engine")
        assert hasattr(pipeline, "executive_engine")
        assert hasattr(pipeline, "experience_engine")

        # Seed a memory for Sarah so MemoryContextProvider retrieves context
        pipeline.memory_encoder.encode_experience(
            person_name="Sarah",
            location="Living Room",
            content="Sarah brought fresh strawberries and medication reminders.",
            context="Daughter visit",
        )

        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert len(actions) >= 1
