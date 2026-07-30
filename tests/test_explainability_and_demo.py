"""
Unit and Integration Tests for Cognitive Decision Timeline, Explainability Engine, and Demo Mode (Phase 19).
"""

import pytest
from src.clinical.decision_timeline import CognitiveDecisionTimeline, ConfidenceLevel
from src.clinical.explainability_engine import ExplainabilityEngine, MemoryProvenance
from src.clinical.caregiver_mode import CaregiverReportGenerator
from src.clinical.demo_mode import AutomaticDemoRunner


def test_confidence_level_mapping():
    """Verify raw score to ConfidenceLevel enum mapping."""
    assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.HIGH
    assert ConfidenceLevel.from_score(0.75) == ConfidenceLevel.MEDIUM
    assert ConfidenceLevel.from_score(0.50) == ConfidenceLevel.LOW
    assert ConfidenceLevel.from_score(0.30) == ConfidenceLevel.UNCERTAIN


def test_cognitive_decision_timeline():
    """Verify CognitiveDecisionTimeline constructs stages and generates markdown."""
    timeline = CognitiveDecisionTimeline(cycle_id=101)
    timeline.add_stage("Vision", "Detected Face", "SCRFD bounding box match", 0.92, 12.5)
    timeline.add_stage("Cognition", "Policy Selected", "Applied One-Step Guidance", 1.0, 0.5)

    data = timeline.to_dict()
    assert data["cycle_id"] == 101
    assert data["stage_count"] == 2
    assert "Cognitive Decision Timeline" in timeline.generate_markdown()


def test_explainability_engine_non_technical():
    """Verify ExplainabilityEngine produces human-readable strings without raw vector math."""
    exp_id = ExplainabilityEngine.explain_identity_match("Riya", 0.90, is_confirmed=True)
    assert "Riya" in exp_id
    assert "High Confidence" in exp_id
    assert "vector" not in exp_id.lower()

    exp_mem = ExplainabilityEngine.explain_memory_retrieval("glasses", found=False)
    assert "haven't seen your glasses" in exp_mem


def test_cognitive_safety_rule():
    """Verify safety check suppresses identity assignment for low confidence scores."""
    name, safe, msg = ExplainabilityEngine.apply_cognitive_safety_checks("Unknown Person", 0.35)
    assert not safe
    assert name is None
    assert "SAFETY RULE ENFORCED" in msg


def test_automatic_demo_runner():
    """Verify AutomaticDemoRunner executes all scenarios successfully."""
    runner = AutomaticDemoRunner()
    res = runner.run_all_scenarios()
    assert res["status"] == "PASS"
    assert len(res["timelines"]) == 3
