from deployment.configs.config_manager import ConfigManager, DeploymentProfile


def test_runtime_profile_enum_values():
    assert DeploymentProfile.SIMULATION.value == "Simulation"
    assert DeploymentProfile.PRODUCTION.value == "Production Edge"

    cm = ConfigManager(profile_override=DeploymentProfile.PRODUCTION)
    assert cm.get_setting("log_level") == "WARNING"
