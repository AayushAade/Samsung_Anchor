from deployment.health.health_checker import HealthChecker, HealthStatus


def test_health_checker_evaluations():
    hc = HealthChecker()
    health_dict = hc.check_health()

    assert health_dict["overall_status"] == HealthStatus.HEALTHY.value

    hc.set_component_health("runtime_ready", False)
    hc.set_component_health("perception_ready", False)
    hc.set_component_health("cognition_ready", False)

    assert hc.get_overall_status() == HealthStatus.CRITICAL
