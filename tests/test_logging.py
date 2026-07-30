from deployment.logging.structured_logger import StructuredLogger


def test_structured_logger_formatting():
    logger = StructuredLogger(module_name="TestLogger")
    log_entry = logger.info("System booted successfully", component="Runtime")

    assert log_entry["level"] == "INFO"
    assert log_entry["module"] == "TestLogger"
    assert log_entry["context"]["component"] == "Runtime"
    assert len(logger.get_recent_logs()) == 1
