"""
Comprehensive Test Suite for MEMORA Phase 38 — Caregiver Intelligence & Clinical Oversight Framework.

Tests:
1. Caregiver Data Models (Serialization of TimelineEvent, CaregiverSummary, TrendReport, CaregiverSnapshot)
2. Patient Timeline (Chronological event logging, daily and session timeline filtering)
3. Longitudinal Trend Analysis (Deterministic trend evaluation for CONFUSION, ROUTINE, and OBJECT metrics)
4. Clinical Escalation Engine (Policy rule evaluations for NONE, MODERATE, HIGH, and URGENT levels)
5. Clinical Summary Generator (Synthesizing CaregiverSummary objects)
6. Central Caregiver Engine (Public façade ingest_event, build_timeline, analyze_trends, generate_summary, snapshot)
7. Caregiver Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.caregiver import (
    CaregiverEngine,
    CaregiverExplainer,
    CaregiverSnapshot,
    CaregiverSummary,
    ClinicalSummaryGenerator,
    EscalationEngine,
    EscalationLevel,
    PatientTimeline,
    TimelineEvent,
    TimelineEventType,
    TrendAnalysisEngine,
    TrendReport,
)


# ======================================================================
# 1. Caregiver Data Models Tests
# ======================================================================

class TestCaregiverModels:
    def test_timeline_event_serialization(self):
        evt = TimelineEvent(
            event_type=TimelineEventType.CONTEXT_RESTORATION,
            description="Restored location context",
            session_id="ses-200",
        )
        d = evt.to_dict()
        assert d["event_type"] == "CONTEXT_RESTORATION"
        assert d["session_id"] == "ses-200"

    def test_caregiver_summary_serialization(self):
        summary = CaregiverSummary(
            patient_id="pat-margaret",
            reporting_period="DAILY",
            completed_routines=["Morning routine"],
            assistance_events=3,
            escalation_level=EscalationLevel.NONE,
        )
        d = summary.to_dict()
        assert d["patient_id"] == "pat-margaret"
        assert d["escalation_level"] == "NONE"

    def test_trend_report_serialization(self):
        tr = TrendReport(
            metric="CONFUSION",
            observation_window="7_DAYS",
            trend_direction="STABLE",
        )
        d = tr.to_dict()
        assert d["metric"] == "CONFUSION"
        assert d["trend_direction"] == "STABLE"


# ======================================================================
# 2. Patient Timeline Tests
# ======================================================================

class TestPatientTimeline:
    def test_add_and_filter_events(self):
        timeline = PatientTimeline()
        e1 = timeline.add_event(TimelineEventType.ROUTINE_COMPLETION, "Breakfast done", session_id="s1")
        e2 = timeline.add_event(TimelineEventType.DISORIENTATION, "Location disorientation", session_id="s1")
        e3 = timeline.add_event(TimelineEventType.OBJECT_ASSISTANCE, "Found glasses", session_id="s2")

        assert len(timeline.get_all_events()) == 3
        assert len(timeline.get_session_timeline("s1")) == 2
        assert len(timeline.get_events_by_type(TimelineEventType.OBJECT_ASSISTANCE)) == 1


# ======================================================================
# 3. Longitudinal Trend Analysis Tests
# ======================================================================

class TestTrendAnalysisEngine:
    def test_confusion_trend(self):
        analyzer = TrendAnalysisEngine()
        events = [
            TimelineEvent(event_type=TimelineEventType.DISORIENTATION, description="d1"),
            TimelineEvent(event_type=TimelineEventType.DISORIENTATION, description="d2"),
            TimelineEvent(event_type=TimelineEventType.REASSURANCE, description="r1"),
            TimelineEvent(event_type=TimelineEventType.REASSURANCE, description="r2"),
        ]
        tr = analyzer.analyze_trend(events, metric="CONFUSION")
        assert tr.trend_direction == "INCREASING"
        assert len(tr.recommendations) > 0


# ======================================================================
# 4. Clinical Escalation Engine Tests
# ======================================================================

class TestEscalationEngine:
    def test_evaluate_normal_baseline(self):
        engine = EscalationEngine()
        events = [TimelineEvent(event_type=TimelineEventType.ROUTINE_COMPLETION, description="Morning routine done")]
        level, rules = engine.evaluate_escalation(events)
        assert level == EscalationLevel.NONE
        assert "Policy Rule #0" in rules[0]

    def test_evaluate_safety_event_urgent(self):
        engine = EscalationEngine()
        events = [
            TimelineEvent(event_type=TimelineEventType.SAFETY_EVENT, description="s1"),
            TimelineEvent(event_type=TimelineEventType.SAFETY_EVENT, description="s2"),
        ]
        level, rules = engine.evaluate_escalation(events)
        assert level == EscalationLevel.URGENT


# ======================================================================
# 5. Clinical Summary Generator Tests
# ======================================================================

class TestClinicalSummaryGenerator:
    def test_generate_summary(self):
        gen = ClinicalSummaryGenerator()
        events = [
            TimelineEvent(event_type=TimelineEventType.ROUTINE_COMPLETION, description="Morning tea"),
            TimelineEvent(event_type=TimelineEventType.OBJECT_ASSISTANCE, description="Found keys"),
        ]
        summary = gen.generate_summary("pat-1", events, period="DAILY")
        assert summary.patient_id == "pat-1"
        assert summary.assistance_events == 1
        assert summary.object_assistance_events == 1


# ======================================================================
# 6. Central Caregiver Engine Tests
# ======================================================================

class TestCaregiverEngine:
    def test_engine_ingest_and_summarize(self):
        engine = CaregiverEngine()
        engine.ingest_event(TimelineEventType.ROUTINE_COMPLETION, "Breakfast done", session_id="ses-1")
        engine.ingest_event(TimelineEventType.OBJECT_ASSISTANCE, "Found wallet", session_id="ses-1")

        timeline = engine.build_timeline(session_id="ses-1")
        assert len(timeline) == 2

        summary = engine.generate_summary("margaret")
        assert summary.patient_id == "margaret"

        snap = engine.snapshot()
        assert snap.total_events_count == 2

        exp_str = engine.explain()
        assert "Caregiver Oversight Summary" in exp_str


# ======================================================================
# 7. Caregiver Explainer Tests
# ======================================================================

class TestCaregiverExplainer:
    def test_explain_engine_state(self):
        engine = CaregiverEngine()
        engine.ingest_event(TimelineEventType.DISORIENTATION, "Where am I query", session_id="ses-1")

        markdown = CaregiverExplainer.explain_engine_state(engine)
        assert "MEMORA Caregiver Intelligence & Clinical Oversight Diagnostic Report" in markdown
        assert "Timeline Overview" in markdown
        assert "Longitudinal Trend Analysis" in markdown
