from src.clinical.caregiver_manager import CaregiverManager
from src.clinical.clinical_models import Caregiver, CaregiverPermission, CaregiverRole


def test_caregiver_manager_permissions():
    mgr = CaregiverManager()
    primary = mgr.get_primary_caregiver()
    assert primary is not None
    assert primary.name == "Sarah Jenkins"

    assert mgr.check_permission("CG-001", CaregiverPermission.FULL_ACCESS) is True
    assert mgr.check_permission("CG-002", CaregiverPermission.READ_ONLY) is True
    assert mgr.check_permission("CG-002", CaregiverPermission.FULL_ACCESS) is False
