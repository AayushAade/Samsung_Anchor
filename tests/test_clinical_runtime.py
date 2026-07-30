"""
Comprehensive Test Suite for MEMORA Phase 30 — Clinical Runtime, Observability & Deployment Framework.

Tests all Phase 30 modules:
1. Runtime Configuration Profiles (Development, Simulation, Clinical Demo, Production)
2. Service Registry (Service registration & subsystem status tracking)
3. Runtime Scheduler (Periodic task execution)
4. Subsystem Fault Isolation Manager (Error recording & degradation checks)
5. Recovery Orchestrator (Deterministic recovery actions: restart, rebuild, restore)
6. Operational Runtime Metrics Aggregator (CPU, memory, thread utilisation)
7. System-Wide Runtime Health Generator (Unified health reports)
8. Runtime Trace Explainer & Structured Logging Framework (JSON structured logs & trace explanations)
9. Central Runtime Engine (Multi-cycle operational processing, ICognitiveSubsystem compliance)
10. Pipeline Runtime Integration (CognitivePipeline Step 0 & stream emission)
"""

import os
import tempfile
import pytest

from src.core.interfaces import ICognitiveSubsystem
from src.runtime.runtime_configuration import RuntimeConfig, RuntimeConfigurationManager, RuntimeProfile
from src.runtime.service_registry import ServiceRegistry
from src.runtime.runtime_scheduler import RuntimeScheduler
from src.runtime.fault_manager import FaultManager
from src.runtime.recovery_orchestrator import RecoveryActionType, RecoveryOrchestrator
from src.runtime.runtime_metrics import RuntimeMetricsAggregator
from src.runtime.runtime_health import RuntimeHealthGenerator
from src.runtime.runtime_explainer import RuntimeExplainer
from src.runtime.runtime_engine import CentralRuntimeEngine


# ======================================================================
# 1. Runtime Configuration Profile Tests
# ======================================================================

class TestRuntimeConfiguration:
    def test_runtime_configuration_profiles(self):
        mgr = RuntimeConfigurationManager(profile=RuntimeProfile.CLINICAL_DEMO)
        assert mgr.get_config().profile == RuntimeProfile.CLINICAL_DEMO

        prod_cfg = mgr.set_profile(RuntimeProfile.PRODUCTION)
        assert prod_cfg.profile == RuntimeProfile.PRODUCTION
        assert prod_cfg.log_level == "WARNING"


# ======================================================================
# 2. Service Registry Tests
# ======================================================================

class DummyService(ICognitiveSubsystem):
    def initialize(self) -> bool: return True
    def shutdown(self) -> bool: return True
    def process(self, input_data: dict) -> dict: return {}
    def status(self) -> str: return "RUNNING"
    def health(self) -> dict: return {"status": "RUNNING"}
    def metrics(self) -> dict: return {}
    def explain(self) -> str: return "Dummy"


class TestServiceRegistry:
    def test_register_and_health_status(self):
        sr = ServiceRegistry()
        dummy = DummyService()
        sr.register_service("DummyService", dummy)
        assert sr.get_service("DummyService") is not None

        health = sr.get_health_status()
        assert health["overall_health"] == "HEALTHY"
        assert health["registered_services_count"] == 1


# ======================================================================
# 3. Runtime Scheduler & Fault Manager Tests
# ======================================================================

class TestSchedulerAndFaults:
    def test_scheduler_ticks(self):
        sch = RuntimeScheduler()
        executed_flag = []
        sch.add_task("test_task", 1.0, lambda: executed_flag.append(True))
        
        count = sch.tick(current_ts=10.0)
        assert count == 1
        assert len(executed_flag) == 1

    def test_fault_manager(self):
        fm = FaultManager()
        fm.record_fault("ReasoningEngine", Exception("Test Error"))
        assert fm.is_subsystem_degraded("ReasoningEngine", threshold=1) is True
        assert len(fm.get_fault_history()) == 1


# ======================================================================
# 4. Recovery Orchestrator & Metrics Tests
# ======================================================================

class TestRecoveryAndMetrics:
    def test_recovery_orchestrator(self):
        sr = ServiceRegistry()
        dummy = DummyService()
        sr.register_service("DummyService", dummy)

        ro = RecoveryOrchestrator(sr)
        rec = ro.recover_subsystem("DummyService", RecoveryActionType.RESTART_SERVICE)
        assert rec.success is True
        assert len(ro.get_recovery_history()) == 1

    def test_runtime_metrics(self):
        rma = RuntimeMetricsAggregator()
        metrics = rma.capture_metrics()
        assert metrics["memory_rss_mb"] > 0.0
        assert metrics["threads_count"] >= 1


# ======================================================================
# 5. System Health & Explainer Tests
# ======================================================================

class TestHealthAndExplainer:
    def test_generate_health_report(self):
        cfg_mgr = RuntimeConfigurationManager()
        sr = ServiceRegistry()
        fm = FaultManager()
        rma = RuntimeMetricsAggregator()

        report = RuntimeHealthGenerator.generate_health_report(cfg_mgr, sr, fm, rma)
        assert report["overall_status"] == "HEALTHY"

    def test_runtime_explainer(self):
        log_json = RuntimeExplainer.create_structured_log("TestSubsystem", "test_op", "corr-1")
        assert "TestSubsystem" in log_json

        trace_exp = RuntimeExplainer.generate_trace_explanation("trc-1", [{"subsystem": "Vision", "duration_ms": 1.5}])
        assert "MEMORA Distributed Execution Trace" in trace_exp


# ======================================================================
# 6. Central Runtime Engine Tests
# ======================================================================

class TestCentralRuntimeEngine:
    def test_process_cycle(self):
        engine = CentralRuntimeEngine()
        assert isinstance(engine, ICognitiveSubsystem)
        assert engine.initialize() is True

        summary = engine.process_cycle()
        assert summary["cycle"] == 1
        assert "runtime_health" in summary
        assert engine.status() == "RUNNING"
        assert engine.shutdown() is True


# ======================================================================
# 7. Pipeline Runtime Integration Tests
# ======================================================================

class TestPipelineRuntimeIntegration:
    def test_pipeline_instantiates_central_runtime(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_runtime_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "central_runtime")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.central_runtime._cycle_counter == 1
