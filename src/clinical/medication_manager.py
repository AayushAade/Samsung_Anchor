from datetime import datetime, timedelta
from typing import List, Optional, Dict
from src.clinical.clinical_models import MedicationSchedule


def _scheduled_today(scheduled_time: str, now: datetime) -> Optional[datetime]:
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            t = datetime.strptime(scheduled_time.strip(), fmt)
            return now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            continue
    return None


class MedicationManager:
    """
    Manages medication scheduling, dosages, missed dose policies, and reminder windows.

    Schedules must come from the person or their caregiver. MEMORA never infers
    that a dose was taken: only an explicit mark_taken() confirmation clears it.
    The two example schedules are fictional demo data and are loaded only when
    seed_demo_data=True.
    """

    def __init__(self, seed_demo_data: bool = False, grace_minutes: int = 30) -> None:
        self._schedules: Dict[str, MedicationSchedule] = {}
        self.grace = timedelta(minutes=grace_minutes)
        if seed_demo_data:
            self._seed_demo_schedules()

    def _seed_demo_schedules(self) -> None:

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
            medication_name="Blood Pressure (Lisinopril)",
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

    def get_missed_medications(self, now: Optional[datetime] = None) -> List[MedicationSchedule]:
        """
        Doses whose scheduled time (plus a grace period) has passed today without
        an explicit taken confirmation. Doses scheduled later today are not missed.
        Schedules with an unparseable time are reported conservatively as missed.
        """
        now = now or datetime.now()
        missed = []
        for m in self._schedules.values():
            if m.is_taken:
                continue
            due = _scheduled_today(m.scheduled_time, now)
            if due is None or now >= due + self.grace:
                missed.append(m)
        return missed
