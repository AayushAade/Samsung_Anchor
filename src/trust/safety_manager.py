"""
MEMORA Safety Guardrails — Unified Safety Manager.

Evaluates every proposed action from CognitiveKernel before execution.
Enforces 6 configurable safety rules:
  1. Confidence Threshold Check
  2. Identity Consistency & Contradiction Resolution
  3. Working Memory Freshness & Stale-State Check
  4. Reminder Frequency Throttling Check
  5. Evidence Consistency & Contradiction Ratio Check
  6. Quiet Hours & Ambient Rest Check

No action bypasses the Safety Manager.
"""

from __future__ import annotations

from datetime import datetime
import threading
import time
from typing import Any, Dict, List, Optional

from src.cognition.cos.models import CognitiveAction, CognitiveActionType
from src.cognition.goals.models import GoalHypothesis
from src.cognition.context.models import CognitiveContext
from src.clinical.patient_state import PatientState, PatientStateMode
from src.trust.models import (
    SafetyCheckResult,
    SafetyEvaluation,
    SafetyStatus,
)


class SafetyManager:
    """
    Unified Safety Manager enforcing non-bypassable cognitive guardrails.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.35,
        reminder_throttle_seconds: float = 1800.0,  # 30 minutes
        quiet_hours_start: int = 22,  # 10 PM
        quiet_hours_end: int = 7,     # 7 AM
    ) -> None:
        self.min_confidence_threshold = min_confidence_threshold
        self.reminder_throttle_seconds = reminder_throttle_seconds
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end

        # Tracking state for reminder throttling
        self._last_reminder_timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Metrics counters
        self._total_evaluations = 0
        self._approved_count = 0
        self._modified_count = 0
        self._blocked_count = 0

    # ------------------------------------------------------------------
    # Core Public API
    # ------------------------------------------------------------------

    def evaluate_action(
        self,
        action: CognitiveAction,
        context: Optional[CognitiveContext] = None,
        goals: Optional[List[GoalHypothesis]] = None,
        patient_state: Optional[PatientState] = None,
        working_memory_snapshot: Optional[Dict[str, Any]] = None,
    ) -> SafetyEvaluation:
        """
        Evaluate a proposed CognitiveAction against all safety rules.

        Returns
        -------
        SafetyEvaluation
            The final evaluation outcome containing status, check results,
            and final action (original or overridden).
        """
        with self._lock:
            self._total_evaluations += 1

        # Emergency bypass: Emergency actions skip standard restrictions but get audited as ESCALATED
        if patient_state and patient_state.mode == PatientStateMode.EMERGENCY:
            check_res = SafetyCheckResult(
                check_name="EmergencySafetyOverride",
                passed=True,
                reason="Emergency safety trigger active. Escalation permitted.",
                severity="CRITICAL",
            )
            with self._lock:
                self._approved_count += 1
            return SafetyEvaluation(
                status=SafetyStatus.ESCALATED,
                original_action=action,
                final_action=action,
                check_results=[check_res],
                evaluation_reason="Emergency safety escalation override.",
            )

        check_results: List[SafetyCheckResult] = []
        final_action = action
        status = SafetyStatus.APPROVED

        # Rule 1: Confidence Threshold Check
        r1 = self._check_confidence_threshold(action)
        check_results.append(r1)
        if not r1.passed and r1.action_override:
            final_action = r1.action_override
            status = SafetyStatus.DOWNGRADED

        # Rule 2: Identity Consistency & Contradiction Check
        r2 = self._check_identity_consistency(context)
        check_results.append(r2)
        if not r2.passed and r2.action_override:
            final_action = r2.action_override
            status = SafetyStatus.DOWNGRADED

        # Rule 3: Working Memory Freshness Check
        r3 = self._check_working_memory_freshness(action, working_memory_snapshot)
        check_results.append(r3)
        if not r3.passed and r3.action_override:
            final_action = r3.action_override
            status = SafetyStatus.DOWNGRADED

        # Rule 4: Reminder Frequency Throttle Check
        r4 = self._check_reminder_throttle(action, goals)
        check_results.append(r4)
        if not r4.passed and r4.action_override:
            final_action = r4.action_override
            status = SafetyStatus.BLOCKED if action.action_type == CognitiveActionType.SPEAK else SafetyStatus.DOWNGRADED

        # Rule 5: Evidence Consistency Ratio Check
        r5 = self._check_evidence_consistency(goals)
        check_results.append(r5)
        if not r5.passed and r5.action_override:
            final_action = r5.action_override
            status = SafetyStatus.DOWNGRADED

        # Rule 6: Quiet Hours & Rest Check
        r6 = self._check_quiet_hours(action)
        check_results.append(r6)
        if not r6.passed and r6.action_override:
            final_action = r6.action_override
            status = SafetyStatus.MODIFIED

        # Determine overall evaluation status
        failed_checks = [c for c in check_results if not c.passed]
        if not failed_checks:
            eval_reason = "All 6 safety guardrails passed successfully."
            with self._lock:
                self._approved_count += 1
        else:
            reasons = [c.reason for c in failed_checks]
            eval_reason = f"Safety intervention triggered: {'; '.join(reasons)}"
            with self._lock:
                if status == SafetyStatus.BLOCKED:
                    self._blocked_count += 1
                else:
                    self._modified_count += 1

        return SafetyEvaluation(
            status=status,
            original_action=action,
            final_action=final_action,
            check_results=check_results,
            evaluation_reason=eval_reason,
        )

    # ------------------------------------------------------------------
    # Individual Rule Implementations
    # ------------------------------------------------------------------

    def _check_confidence_threshold(self, action: CognitiveAction) -> SafetyCheckResult:
        if action.action_type == CognitiveActionType.REMAIN_SILENT:
            return SafetyCheckResult(
                check_name="ConfidenceThresholdCheck",
                passed=True,
                reason="Action is REMAIN_SILENT; confidence threshold not required.",
            )

        if action.confidence < self.min_confidence_threshold:
            override = CognitiveAction(
                action_type=CognitiveActionType.REMAIN_SILENT,
                reasoning_path=f"SafetyGuardrail: Confidence {action.confidence:.2f} < threshold {self.min_confidence_threshold:.2f} → Downgraded to SILENCE",
                confidence=0.95,
            )
            return SafetyCheckResult(
                check_name="ConfidenceThresholdCheck",
                passed=False,
                reason=f"Action confidence {action.confidence:.2f} is below safety threshold {self.min_confidence_threshold:.2f}.",
                severity="WARNING",
                action_override=override,
            )

        return SafetyCheckResult(
            check_name="ConfidenceThresholdCheck",
            passed=True,
            reason=f"Action confidence {action.confidence:.2f} satisfies safety threshold {self.min_confidence_threshold:.2f}.",
        )

    def _check_identity_consistency(self, context: Optional[CognitiveContext]) -> SafetyCheckResult:
        if not context or not context.identity:
            return SafetyCheckResult(
                check_name="IdentityConsistencyCheck",
                passed=True,
                reason="No identity context provided; skipping check.",
            )

        ident = context.identity
        if ident.confidence < 0.20 and ident.is_known:
            override = CognitiveAction(
                action_type=CognitiveActionType.REMAIN_SILENT,
                reasoning_path="SafetyGuardrail: Suspicious face identity confidence < 0.20 → Downgraded to SILENCE",
                confidence=0.90,
            )
            return SafetyCheckResult(
                check_name="IdentityConsistencyCheck",
                passed=False,
                reason=f"Identity confidence {ident.confidence:.2f} is suspiciously low for known person '{ident.name}'.",
                severity="WARNING",
                action_override=override,
            )

        return SafetyCheckResult(
            check_name="IdentityConsistencyCheck",
            passed=True,
            reason=f"Identity context is consistent for person '{ident.name or 'Unknown'}'.",
        )

    def _check_working_memory_freshness(
        self, action: CognitiveAction, working_memory_snapshot: Optional[Dict[str, Any]]
    ) -> SafetyCheckResult:
        wm_key = action.metadata.get("working_memory_key")
        if not wm_key or not working_memory_snapshot:
            return SafetyCheckResult(
                check_name="WorkingMemoryFreshnessCheck",
                passed=True,
                reason="Action does not rely on working memory slots.",
            )

        slots = working_memory_snapshot.get("slots", {})
        if wm_key in slots and slots[wm_key].get("is_expired", False):
            override = CognitiveAction(
                action_type=CognitiveActionType.REMAIN_SILENT,
                reasoning_path=f"SafetyGuardrail: Referenced working memory slot '{wm_key}' is expired → Downgraded to SILENCE",
                confidence=0.90,
            )
            return SafetyCheckResult(
                check_name="WorkingMemoryFreshnessCheck",
                passed=False,
                reason=f"Referenced working memory slot '{wm_key}' is expired.",
                severity="WARNING",
                action_override=override,
            )

        return SafetyCheckResult(
            check_name="WorkingMemoryFreshnessCheck",
            passed=True,
            reason=f"Working memory slot '{wm_key}' is fresh.",
        )

    def _check_reminder_throttle(
        self, action: CognitiveAction, goals: Optional[List[GoalHypothesis]]
    ) -> SafetyCheckResult:
        if action.action_type not in (CognitiveActionType.SPEAK, CognitiveActionType.ASK_CLARIFICATION):
            return SafetyCheckResult(
                check_name="ReminderFrequencyThrottleCheck",
                passed=True,
                reason="Action is non-verbal; throttling not applicable.",
            )

        goal_name = action.metadata.get("goal") or "GeneralReminder"
        now = time.time()

        with self._lock:
            last_sent = self._last_reminder_timestamps.get(goal_name, 0.0)

        elapsed = now - last_sent
        if elapsed < self.reminder_throttle_seconds:
            remaining_mins = (self.reminder_throttle_seconds - elapsed) / 60.0
            override = CognitiveAction(
                action_type=CognitiveActionType.REMAIN_SILENT,
                reasoning_path=f"SafetyGuardrail: Reminder for '{goal_name}' throttled (remaining {remaining_mins:.1f} mins) → Downgraded to SILENCE",
                confidence=0.90,
            )
            return SafetyCheckResult(
                check_name="ReminderFrequencyThrottleCheck",
                passed=False,
                reason=f"Reminder for '{goal_name}' was sent {elapsed / 60.0:.1f} mins ago; throttled for {self.reminder_throttle_seconds / 60.0:.0f} mins window.",
                severity="INFO",
                action_override=override,
            )

        # Update last sent timestamp if action passes
        with self._lock:
            self._last_reminder_timestamps[goal_name] = now

        return SafetyCheckResult(
            check_name="ReminderFrequencyThrottleCheck",
            passed=True,
            reason=f"Reminder for '{goal_name}' is within allowed frequency window.",
        )

    def _check_evidence_consistency(self, goals: Optional[List[GoalHypothesis]]) -> SafetyCheckResult:
        if not goals:
            return SafetyCheckResult(
                check_name="EvidenceConsistencyCheck",
                passed=True,
                reason="No goals provided for evidence ratio check.",
            )

        for g in goals:
            sup_weight = sum(e.weight for e in (g.supporting_evidence or []))
            con_weight = sum(e.weight for e in (g.contradicting_evidence or []))

            if con_weight > sup_weight and con_weight > 0.5:
                override = CognitiveAction(
                    action_type=CognitiveActionType.REMAIN_SILENT,
                    reasoning_path=f"SafetyGuardrail: Goal '{g.name}' has contradicting evidence ({con_weight:.2f}) > supporting ({sup_weight:.2f}) → Downgraded to SILENCE",
                    confidence=0.90,
                )
                return SafetyCheckResult(
                    check_name="EvidenceConsistencyCheck",
                    passed=False,
                    reason=f"Goal '{g.name}' has contradicting evidence ({con_weight:.2f}) exceeding supporting evidence ({sup_weight:.2f}).",
                    severity="WARNING",
                    action_override=override,
                )

        return SafetyCheckResult(
            check_name="EvidenceConsistencyCheck",
            passed=True,
            reason="Goal evidence ratios are consistent.",
        )

    def _check_quiet_hours(self, action: CognitiveAction) -> SafetyCheckResult:
        if action.action_type != CognitiveActionType.SPEAK:
            return SafetyCheckResult(
                check_name="QuietHoursCheck",
                passed=True,
                reason="Action is non-speech; quiet hours check passed.",
            )

        current_hour = datetime.now().hour
        is_quiet = False
        if self.quiet_hours_start > self.quiet_hours_end:
            # Overnight quiet hours (e.g. 22:00 to 07:00)
            is_quiet = current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            is_quiet = self.quiet_hours_start <= current_hour < self.quiet_hours_end

        if is_quiet:
            override = CognitiveAction(
                action_type=CognitiveActionType.REMAIN_SILENT,
                reasoning_path=f"SafetyGuardrail: Quiet hours active ({self.quiet_hours_start}:00-{self.quiet_hours_end}:00) → Spoken action converted to SILENCE",
                confidence=0.95,
            )
            return SafetyCheckResult(
                check_name="QuietHoursCheck",
                passed=False,
                reason=f"Current time ({current_hour}:00) is within quiet hours window ({self.quiet_hours_start}:00-{self.quiet_hours_end}:00).",
                severity="INFO",
                action_override=override,
            )

        return SafetyCheckResult(
            check_name="QuietHoursCheck",
            passed=True,
            reason="Current time is outside quiet hours window.",
        )

    # ------------------------------------------------------------------
    # Metrics & Reset
    # ------------------------------------------------------------------

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_evaluations": self._total_evaluations,
                "approved_count": self._approved_count,
                "modified_count": self._modified_count,
                "blocked_count": self._blocked_count,
                "min_confidence_threshold": self.min_confidence_threshold,
                "reminder_throttle_minutes": self.reminder_throttle_seconds / 60.0,
                "quiet_hours": f"{self.quiet_hours_start}:00-{self.quiet_hours_end}:00",
            }

    def reset(self) -> None:
        with self._lock:
            self._last_reminder_timestamps.clear()
            self._total_evaluations = 0
            self._approved_count = 0
            self._modified_count = 0
            self._blocked_count = 0
