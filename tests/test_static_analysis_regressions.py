"""
Regression tests for runtime NameErrors found by static analysis (ruff F821).
Each of these code paths raised as soon as it executed.
"""

from __future__ import annotations

from src.cognition.assistance.history import ConfidenceHistory
from src.cognition.goals.models import GoalState
from src.cognition.goals.reasoner import HeuristicGoalReasoner
from src.trust.audit_framework import AuditFramework
from src.trust.privacy_manager import PrivacyManager


def test_confidence_history_clear():
    h = ConfidenceHistory()
    h.clear()  # previously: TypeError (missing self)


def test_conversational_goal_hypothesis_uses_goal_state():
    class Ctx:
        working_memory = {"previous_user_message": "where are my glasses"}
        memory = identity = temporal = social = continuity = assistance = conversation = None
        timestamp = None
    hyps = HeuristicGoalReasoner().infer(Ctx())
    assert any(h.name == "Locate Glasses" and h.state == GoalState.DETECTED for h in hyps)


def test_audit_retention_purge_runs():
    audit = AuditFramework()
    counts = PrivacyManager().purge_expired_records(audit_framework=audit)  # previously: NameError
    assert "audit_records" in counts
