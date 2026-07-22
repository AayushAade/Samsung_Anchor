from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class CaregiverRole(Enum):
    PRIMARY_CAREGIVER = "Primary Caregiver"
    FAMILY = "Family Member"
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    VOLUNTEER = "Volunteer"


class CaregiverPermission(Enum):
    FULL_ACCESS = "Full Access"
    READ_ONLY = "Read Only"
    NOTIFICATIONS_ONLY = "Notifications Only"
    EMERGENCY_ONLY = "Emergency Only"


@dataclass
class Caregiver:
    caregiver_id: str
    name: str
    role: CaregiverRole
    permission: CaregiverPermission = CaregiverPermission.FULL_ACCESS
    contact_phone: str = ""
    notification_preference: str = "Instant Alert"
    is_available: bool = True


@dataclass
class PatientProfile:
    patient_id: str = "P-001"
    preferred_name: str = "Eleanor"
    age: int = 76
    primary_diagnosis: str = "Alzheimer's Disease (Mild to Moderate)"
    stage: str = "Stage 4 (Mild Dementia)"
    primary_language: str = "English"
    emergency_contacts: List[str] = field(default_factory=lambda: ["Sarah Jenkins (Daughter) - 555-0192", "Dr. Robert Chen - 555-0144"])
    primary_caregiver: str = "Sarah Jenkins"
    primary_physician: str = "Dr. Robert Chen"
    known_allergies: List[str] = field(default_factory=lambda: ["Penicillin", "Sulfa drugs"])
    medical_conditions: List[str] = field(default_factory=lambda: ["Hypertension", "Mild Memory Impairment"])
    communication_preferences: str = "Calm tone, short sentences, gentle visual prompts"
    daily_routine_preferences: str = "Morning tea at 8:30 AM, afternoon garden walk at 3:00 PM"


@dataclass
class MedicationSchedule:
    med_id: str
    medication_name: str
    dose: str
    scheduled_time: str
    instructions: str
    is_taken: bool = False
    missed_dose_policy: str = "Notify primary caregiver if delayed by 60 mins"
    caregiver_notify_rule: str = "Immediate alert on missed dose"


class AppointmentStatus(Enum):
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


@dataclass
class Appointment:
    appt_id: str
    title: str
    appointment_type: str
    scheduled_time: str
    location: str
    provider_name: str
    status: AppointmentStatus = AppointmentStatus.UPCOMING


class ConsentFeature(Enum):
    VOICE_RECORDING = "Voice Recording"
    CONVERSATION_STORAGE = "Conversation Storage"
    CAREGIVER_ACCESS = "Caregiver Access"
    DOCTOR_ACCESS = "Doctor Access"
    MEMORY_RETENTION = "Memory Retention"
    ANALYTICS = "Analytics"


@dataclass
class ConsentRecord:
    feature: ConsentFeature
    granted: bool = True
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class EmergencyPriority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class EmergencyState:
    active: bool = False
    trigger_reason: str = "None"
    priority: EmergencyPriority = EmergencyPriority.LOW
    immediate_action: str = "Normal Observation"
    caregiver_notified: bool = False
    workflow_name: str = "Standard Routine"


@dataclass
class DecisionExplanation:
    reason: str
    presence_eval: str
    assistance_eval: str
    strategy_selected: str
    dignity_check_passed: bool = True


@dataclass
class AuditEntry:
    timestamp: str
    reason: str
    module: str
    decision: str
    assistance_level: int
    presence_state: str
    strategy: str
    outcome: str
