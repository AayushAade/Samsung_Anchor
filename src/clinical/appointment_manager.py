from typing import List, Dict
from src.clinical.clinical_models import Appointment, AppointmentStatus


class AppointmentManager:
    """
    Tracks clinical appointments, doctor consultations, therapy, and family events.
    """

    def __init__(self) -> None:
        self._appointments: Dict[str, Appointment] = {}

        # Seed appointment
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

    def get_upcoming_appointments(self) -> List[Appointment]:
        return [a for a in self._appointments.values() if a.status == AppointmentStatus.UPCOMING]

    def get_all_appointments(self) -> List[Appointment]:
        return list(self._appointments.values())
