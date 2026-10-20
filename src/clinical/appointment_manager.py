from datetime import datetime
from typing import Any, List, Dict, Optional
from src.clinical.clinical_models import Appointment, AppointmentStatus


def _friendly(dt: datetime) -> str:
    return f"on {dt.strftime('%A')}, {dt.strftime('%B')} {dt.day} at {dt.strftime('%I:%M %p').lstrip('0')}"


class AppointmentManager:
    """
    Tracks clinical appointments, doctor consultations, therapy, and family events.
    """

    def __init__(self, seed_demo_data: bool = False, store: Any = None) -> None:
        self._appointments: Dict[str, Appointment] = {}
        self._when: Dict[str, datetime] = {}
        self.store = store
        if store is not None:
            for item in store.items("appointment"):
                try:
                    when = datetime.fromisoformat(item.scheduled_time)
                except (TypeError, ValueError):
                    continue
                self._register(item.item_id, item.title, when, item.detail or "")
        # The example appointment is fictional demo data; real appointments are
        # entered by the person or their carer.
        if seed_demo_data:
            self._seed_demo_appointment()

    def _seed_demo_appointment(self) -> None:
        doctor_visit = Appointment(
            appt_id="APPT-001",
            title="Neurology Checkup",
            appointment_type="Doctor Visit",
            scheduled_time="Tomorrow at 10:30 AM",
            location="Memory Clinic, Suite 400",
            provider_name="Dr. Robert Chen",
            status=AppointmentStatus.UPCOMING,
        )
        self._appointments[doctor_visit.appt_id] = doctor_visit

    def add_appointment(self, appointment: Appointment) -> None:
        self._appointments[appointment.appt_id] = appointment

    def _register(self, appt_id: str, title: str, when: datetime, location: str) -> Appointment:
        appt = Appointment(appt_id=appt_id, title=title, appointment_type="Entered by person/caregiver",
                           scheduled_time=_friendly(when), location=location, provider_name="")
        self._appointments[appt_id] = appt
        self._when[appt_id] = when
        return appt

    def add_scheduled(self, title: str, when: datetime, location: str = "",
                      entered_by: str = "user (chat)") -> Appointment:
        appt_id = (self.store.add_item("appointment", title, when.isoformat(), location, entered_by)
                   if self.store is not None else f"appt_{len(self._appointments) + 1}")
        return self._register(appt_id, title, when, location)

    def remove_appointment(self, appt_id: str) -> bool:
        existed = self._appointments.pop(appt_id, None) is not None
        self._when.pop(appt_id, None)
        if existed and self.store is not None:
            self.store.remove_item(appt_id)
        return existed

    def get_upcoming_appointments(self, now: Optional[datetime] = None) -> List[Appointment]:
        now = now or datetime.now()
        upcoming = [a for a in self._appointments.values() if a.status == AppointmentStatus.UPCOMING
                    and (a.appt_id not in self._when or self._when[a.appt_id] >= now)]
        return sorted(upcoming, key=lambda a: self._when.get(a.appt_id, datetime.max))

    def get_all_appointments(self) -> List[Appointment]:
        return list(self._appointments.values())
