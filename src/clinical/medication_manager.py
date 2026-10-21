from datetime import date, datetime, timedelta
from typing import Any, List, Optional, Dict
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

    def __init__(self, seed_demo_data: bool = False, grace_minutes: int = 30, store: Any = None) -> None:
        self._schedules: Dict[str, MedicationSchedule] = {}
        self.grace = timedelta(minutes=grace_minutes)
        # Optional CareStore: schedules entered by the person/caregiver persist across restarts.
        self.store = store
        self._reported_on: Dict[str, date] = {}
        if seed_demo_data:
            self._seed_demo_schedules()
        if store is not None:
            for item in store.items("medication"):
                self._schedules[item.item_id] = MedicationSchedule(
                    med_id=item.item_id, medication_name=item.title, dose=item.detail or "",
                    scheduled_time=item.scheduled_time or "", instructions=f"Entered by {item.entered_by}")

    def add_scheduled(self, name: str, scheduled_time: str, dose: str = "",
                      entered_by: str = "user (chat)") -> MedicationSchedule:
        """Add a daily schedule entered by the person or a caregiver (persisted when a store is set)."""
        if self.store is not None:
            self.store._require_consent()
        if _scheduled_today(scheduled_time, datetime.now()) is None:
            raise ValueError(f"Unrecognised time '{scheduled_time}'. Use HH:MM, e.g. 08:30 or 20:00.")
        if self.store is not None:
            med_id = self.store.add_item("medication", name, scheduled_time, dose, entered_by)
        else:
            med_id = f"med_{len(self._schedules) + 1}"
        sched = MedicationSchedule(med_id=med_id, medication_name=name, dose=dose,
                                   scheduled_time=scheduled_time, instructions=f"Entered by {entered_by}")
        self._schedules[med_id] = sched
        return sched

    def report_taken(self, med_id: str, source: str = "user statement", when: Optional[datetime] = None) -> bool:
        """
        Record that the person *said* they took a dose today. This is a report,
        not a verification, and is stored as such.
        """
        if med_id not in self._schedules:
            return False
        if self.store is not None:
            self.store._require_consent()
        when = when or datetime.now()
        self._reported_on[med_id] = when.date()
        if self.store is not None:
            self.store.record_event(med_id, "REPORTED_TAKEN", source, when)
        return True

    def reported_taken_today(self, med_id: str, now: Optional[datetime] = None) -> bool:
        today = (now or datetime.now()).date()
        if self._reported_on.get(med_id) == today:
            return True
        return bool(self.store is not None and self.store.last_event(med_id, "REPORTED_TAKEN", on=today))

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

    def remove_medication(self, med_id: str) -> bool:
        existed = self._schedules.pop(med_id, None) is not None
        if existed and self.store is not None:
            self.store.remove_item(med_id)
        return existed

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
            if m.is_taken or self.reported_taken_today(m.med_id, now):
                continue
            due = _scheduled_today(m.scheduled_time, now)
            if due is None or now >= due + self.grace:
                missed.append(m)
        return missed
