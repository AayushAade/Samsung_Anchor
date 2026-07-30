from typing import List, Optional, Dict
from src.clinical.clinical_models import Caregiver, CaregiverPermission, CaregiverRole


class CaregiverManager:
    """
    Manages multi-caregiver access, roles, and notification preferences.
    """

    def __init__(self) -> None:
        self._caregivers: Dict[str, Caregiver] = {}

        # Seed primary caregiver
        primary = Caregiver(
            caregiver_id="CG-001",
            name="Sarah Jenkins",
            role=CaregiverRole.PRIMARY_CAREGIVER,
            permission=CaregiverPermission.FULL_ACCESS,
            contact_phone="555-0192",
            notification_preference="Instant Push Alert",
        )
        self._caregivers[primary.caregiver_id] = primary

        # Seed physician
        physician = Caregiver(
            caregiver_id="CG-002",
            name="Dr. Robert Chen",
            role=CaregiverRole.DOCTOR,
            permission=CaregiverPermission.READ_ONLY,
            contact_phone="555-0144",
            notification_preference="Clinical Summary Email",
        )
        self._caregivers[physician.caregiver_id] = physician

    def add_caregiver(self, caregiver: Caregiver) -> None:
        self._caregivers[caregiver.caregiver_id] = caregiver

    def get_caregiver(self, caregiver_id: str) -> Optional[Caregiver]:
        return self._caregivers.get(caregiver_id)

    def get_all_caregivers(self) -> List[Caregiver]:
        return list(self._caregivers.values())

    def get_primary_caregiver(self) -> Optional[Caregiver]:
        for cg in self._caregivers.values():
            if cg.role == CaregiverRole.PRIMARY_CAREGIVER:
                return cg
        return None

    def check_permission(self, caregiver_id: str, required_permission: CaregiverPermission) -> bool:
        cg = self.get_caregiver(caregiver_id)
        if not cg:
            return False
        if cg.permission == CaregiverPermission.FULL_ACCESS:
            return True
        return cg.permission == required_permission
