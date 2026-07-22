from src.clinical.clinical_models import EmergencyPriority, EmergencyState


class EmergencyManager:
    """
    Deterministic emergency workflow manager.
    Coordinates fall detection, medical emergency, and disorientation overrides.
    """

    def __init__(self) -> None:
        self._state = EmergencyState(
            active=False,
            trigger_reason="None",
            priority=EmergencyPriority.LOW,
            immediate_action="Normal Observation",
            caregiver_notified=False,
            workflow_name="Standard Routine",
        )

    def trigger_emergency(
        self,
        reason: str,
        priority: EmergencyPriority = EmergencyPriority.HIGH,
        immediate_action: str = "Prompt direct assistance and alert caregiver",
        workflow_name: str = "Medical Safety Protocol",
    ) -> EmergencyState:
        self._state = EmergencyState(
            active=True,
            trigger_reason=reason,
            priority=priority,
            immediate_action=immediate_action,
            caregiver_notified=True,
            workflow_name=workflow_name,
        )
        return self._state

    def clear_emergency(self) -> EmergencyState:
        self._state = EmergencyState(
            active=False,
            trigger_reason="None",
            priority=EmergencyPriority.LOW,
            immediate_action="Normal Observation",
            caregiver_notified=False,
            workflow_name="Standard Routine",
        )
        return self._state

    def get_current_state(self) -> EmergencyState:
        return self._state
