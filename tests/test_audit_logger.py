from src.clinical.audit_logger import AuditLogger


def test_audit_logger_entries():
    logger = AuditLogger()
    entry = logger.log_intervention(
        reason="Test routine",
        module="TestModule",
        decision="Silent Observation",
        assistance_level=0,
        presence_state="PERMITTED",
        strategy="Supportive Silence",
    )

    assert entry.reason == "Test routine"
    assert len(logger.get_recent_entries()) == 1
