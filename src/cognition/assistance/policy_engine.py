from typing import Optional, Tuple
from src.cognition.assistance.history import ConfidenceHistory
from src.cognition.assistance.models import AssistanceContext, AssistanceLevel
from src.interaction.events import PresenceEvent


class AssistancePolicyEngine:
    """
    Deterministic Policy Engine for Graduated Assistance.
    Calculates the minimum effective support level (Level 0 - Level 5) to preserve independence.
    """

    def __init__(self, history: Optional[ConfidenceHistory] = None) -> None:
        self.history = history or ConfidenceHistory()

    def evaluate_level(
        self,
        event: PresenceEvent,
        has_medical_commitment: bool = False,
        has_active_goals: bool = False,
        has_known_memories: bool = False,
    ) -> AssistanceContext:
        """
        Deterministically evaluates the appropriate assistance level.
        """
        person_id = event.face_id or "unknown"
        last_support = self.history.get_last_event_for_person(person_id)

        # 1. Level 5: Safety Intervention
        if has_medical_commitment:
            level = AssistanceLevel.LEVEL_5
            rationale = "Critical medical commitment active. Providing direct safety instruction."
            self.history.log_event(person_id, level, rationale, outcome="DELIVERED")
            return AssistanceContext(
                level=level,
                level_code=level.value,
                level_label=level.label,
                rationale=rationale,
                escalation_triggered=True,
                support_history_count=len(self.history.get_recent_events(person_id)),
            )

        # 2. Level 4: Direct Assistance (Escalation from Level 3)
        if last_support and last_support.level == AssistanceLevel.LEVEL_3 and last_support.outcome == "PENDING":
            level = AssistanceLevel.LEVEL_4
            rationale = "Previous context restoration cue unresolved. Escalating to step-by-step direct guidance."
            self.history.log_event(person_id, level, rationale, outcome="DELIVERED")
            return AssistanceContext(
                level=level,
                level_code=level.value,
                level_label=level.label,
                rationale=rationale,
                escalation_triggered=True,
                support_history_count=len(self.history.get_recent_events(person_id)),
            )

        # 3. Level 3: Context Restoration
        if has_known_memories or (event.name and event.relationship):
            level = AssistanceLevel.LEVEL_3
            rationale = "Recognized person / memory context present. Providing warm context restoration."
            self.history.log_event(person_id, level, rationale, outcome="PENDING")
            return AssistanceContext(
                level=level,
                level_code=level.value,
                level_label=level.label,
                rationale=rationale,
                escalation_triggered=False,
                support_history_count=len(self.history.get_recent_events(person_id)),
            )

        # 4. Level 2: Gentle Hint
        if has_active_goals:
            level = AssistanceLevel.LEVEL_2
            rationale = "Active user goal inferred. Providing subtle indirect hint to preserve autonomy."
            self.history.log_event(person_id, level, rationale, outcome="DELIVERED")
            return AssistanceContext(
                level=level,
                level_code=level.value,
                level_label=level.label,
                rationale=rationale,
                escalation_triggered=False,
                support_history_count=len(self.history.get_recent_events(person_id)),
            )

        # 5. Level 1: Encourage
        if event.name:
            level = AssistanceLevel.LEVEL_1
            rationale = "Recognized user present. Providing light positive encouragement."
            self.history.log_event(person_id, level, rationale, outcome="DELIVERED")
            return AssistanceContext(
                level=level,
                level_code=level.value,
                level_label=level.label,
                rationale=rationale,
                escalation_triggered=False,
                support_history_count=len(self.history.get_recent_events(person_id)),
            )

        # 6. Level 0: Observe
        level = AssistanceLevel.LEVEL_0
        rationale = "No active intervention required. Patient navigating routine independently."
        return AssistanceContext(
            level=level,
            level_code=level.value,
            level_label=level.label,
            rationale=rationale,
            escalation_triggered=False,
            support_history_count=len(self.history.get_recent_events(person_id)),
        )
