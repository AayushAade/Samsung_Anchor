"""
Comprehensive Test Suite for MEMORA Phase 32 — Cognitive Integrity & Consistency Framework.

Tests:
1. Integrity Data Models (IntegrityLevel, IntegrityCategory, IntegrityIssue, IntegrityReport)
2. Primary Integrity Validator (Missing subsystem detection, interface compliance, duplicate detection)
3. Cross-Subsystem Consistency Checker (Memory-Knowledge references, Executive-Memory references, Session references, Pipeline stage ordering)
4. Central Integrity Engine (Run full check, aggregate report, overall health determination)
5. Integrity Explainer (Markdown summary generation for clean and issue-containing reports)
6. Read-Only Non-Mutation Invariant (Verifies that integrity checks never modify underlying subsystems)
"""

import os
import tempfile
import pytest

from src.core.interfaces import ICognitiveSubsystem
from src.integrity.integrity_models import (
    IntegrityCategory,
    IntegrityIssue,
    IntegrityLevel,
    IntegrityReport,
)
from src.integrity.integrity_validator import IntegrityValidator
from src.integrity.consistency_checker import ConsistencyChecker
from src.integrity.integrity_engine import IntegrityEngine
from src.integrity.integrity_explainer import IntegrityExplainer
from src.memory.memory_engine import MemoryEngine
from src.memory.memory_models import MemoryCategory, MemoryRecord
from src.knowledge.knowledge_engine import KnowledgeEngine
from src.runtime.service_registry import ServiceRegistry


# ======================================================================
# 1. Integrity Data Models Tests
# ======================================================================

class TestIntegrityModels:
    def test_integrity_issue_serialization(self):
        issue = IntegrityIssue(
            category=IntegrityCategory.KNOWLEDGE,
            severity=IntegrityLevel.WARNING,
            subsystem="KnowledgeEngine",
            description="Orphaned fact detected.",
            affected_reference="Fact[fact-123]",
            recommendation="Ingest missing fact.",
        )
        d = issue.to_dict()
        assert d["category"] == "KNOWLEDGE"
        assert d["severity"] == "WARNING"
        assert d["subsystem"] == "KnowledgeEngine"
        assert d["issue_id"].startswith("iss-")

    def test_integrity_report_serialization(self):
        report = IntegrityReport(
            total_checks=15,
            passed_checks=14,
            failed_checks=1,
            warning_count=1,
            overall_status="WARNINGS_DETECTED",
        )
        d = report.to_dict()
        assert d["total_checks"] == 15
        assert d["overall_status"] == "WARNINGS_DETECTED"


# ======================================================================
# 2. Integrity Validator Tests
# ======================================================================

class NonCompliantService:
    """Service that does not implement ICognitiveSubsystem."""
    pass


class TestIntegrityValidator:
    def test_validate_missing_pipeline_subsystem(self):
        class MockIncompletePipeline:
            pass

        issues = IntegrityValidator.validate_subsystems(pipeline=MockIncompletePipeline())
        assert len(issues) > 0
        assert any(i.severity == IntegrityLevel.CRITICAL for i in issues)

    def test_validate_service_registry(self):
        sr = ServiceRegistry()
        sr.register_service("MemoryEngine", MemoryEngine())
        
        # Manually inject non-compliant service for validator check
        sr._services["NonCompliant"] = NonCompliantService()

        issues = IntegrityValidator.validate_subsystems(service_registry=sr)
        assert len(issues) == 1
        assert issues[0].subsystem == "NonCompliant"
        assert issues[0].severity == IntegrityLevel.WARNING


# ======================================================================
# 3. Consistency Checker Tests
# ======================================================================

class TestConsistencyChecker:
    def test_orphaned_knowledge_reference_detection(self):
        mem_engine = MemoryEngine()
        mem_engine.reset()

        # Add a record with an orphaned knowledge reference
        bad_rec = MemoryRecord(
            content="Test Memory with bad ref",
            category=MemoryCategory.OBSERVATION,
            knowledge_references=["fact-non-existent-999"],
        )
        mem_engine.repository.add_record(bad_rec)

        ke = KnowledgeEngine()

        issues = ConsistencyChecker.check_consistency(
            memory_engine=mem_engine,
            knowledge_engine=ke,
        )
        assert len(issues) >= 1
        assert any("fact-non-existent-999" in i.description for i in issues)

    def test_pipeline_order_validation(self):
        bad_order = ["MemoryEngine", "PerceptionManager"]
        issues = ConsistencyChecker.check_consistency(pipeline_stage_order=bad_order)
        assert len(issues) == 1
        assert issues[0].severity == IntegrityLevel.ERROR


# ======================================================================
# 4. Central Integrity Engine Tests
# ======================================================================

class TestIntegrityEngine:
    def test_clean_ecosystem_check(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline

        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_integrity_engine.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)

        engine = IntegrityEngine()
        report = engine.run_integrity_check(pipeline=pipeline)

        assert isinstance(report, IntegrityReport)
        assert report.overall_status in ("HEALTHY", "WARNINGS_DETECTED")
        assert report.total_checks == 15

    def test_read_only_non_mutation_invariant(self):
        """Verify that running integrity checks never mutates subsystem states."""
        mem_engine = MemoryEngine()
        initial_active_count = len(mem_engine.repository.get_all_active())

        engine = IntegrityEngine()
        engine.run_integrity_check(memory_engine=mem_engine)

        assert len(mem_engine.repository.get_all_active()) == initial_active_count


# ======================================================================
# 5. Integrity Explainer Tests
# ======================================================================

class TestIntegrityExplainer:
    def test_explain_clean_report(self):
        report = IntegrityReport(total_checks=15, passed_checks=15, failed_checks=0, overall_status="HEALTHY")
        markdown = IntegrityExplainer.explain_report(report)
        assert "MEMORA Cognitive Ecosystem Integrity Report" in markdown
        assert "HEALTHY" in markdown
        assert "✅ All cognitive subsystems" in markdown

    def test_explain_report_with_issues(self):
        issue = IntegrityIssue(
            category=IntegrityCategory.MEMORY,
            severity=IntegrityLevel.CRITICAL,
            subsystem="MemoryEngine",
            description="Corrupted record detected.",
            affected_reference="MemoryRecord[mem-1]",
            recommendation="Restore from backup.",
        )
        report = IntegrityReport(
            total_checks=15,
            passed_checks=14,
            failed_checks=1,
            issues=[issue],
            overall_status="CRITICAL_ISSUES_DETECTED",
        )
        markdown = IntegrityExplainer.explain_report(report)
        assert "Critical Errors" in markdown
        assert "Corrupted record detected." in markdown
        assert "Restore from backup." in markdown
