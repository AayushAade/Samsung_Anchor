from typing import List, Optional, Dict
from src.clinical.clinical_models import MedicationSchedule


class MedicationManager:
    """
    Manages medication scheduling, dosages, missed dose policies, and reminder windows.
    """

    def __init__(self) -> None:
        self._schedules: Dict[str, MedicationSchedule] = {}

        # Seed morning medication
        morning_med = MedicationSchedule(
            med_id="MED-001",
            medication_name="Donepezil (Aricept)",
            dose="10 mg",
            scheduled_time="09:00 AM",
            instructions="Take 1 tablet with water after morning meal",
            is_taken=False,
            missed_dose_policy="Remind twice at 15-min intervals, then notify caregiver",
            caregiver_notify_rule="Notify Sarah Jenkins if unconfirmed by 10:00 AM",
        )
        self._schedules[morning_med.med_id] = morning_med

        # Seed evening medication
        evening_med = MedicationSchedule(
            med_id="MED-002",
            medication_name="Blood Pressure (Lisnopril)",
            dose="5 mg",
            scheduled_time="06:00 PM",
            instructions="Take 1 tablet before dinner",
            is_taken=False,
            missed_dose_policy="Remind at 06:15 PM",
            caregiver_notify_rule="Notify Sarah Jenkins if unconfirmed by 07:00 PM",
        )
        self._schedules[evening_med.med_id] = evening_med

    def add_medication(self, schedule: MedicationSchedule) -> None:
        self._schedules[schedule.med_id] = schedule

    def get_all_schedules(self) -> List[MedicationSchedule]:
        return list(self._schedules.values())

    def mark_taken(self, med_id: str) -> bool:
        med = self._schedules.get(med_id)
        if med:
            med.is_taken = True
            return True
        return False

    def get_missed_medications(self) -> List[MedicationSchedule]:
        return [m for m in self._schedules.values() if not m.is_taken]
