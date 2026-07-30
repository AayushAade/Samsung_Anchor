from deployment.configs.config_manager import ConfigManager, DeploymentProfile
from src.runtime.runtime_models import RuntimeMode


def test_configuration_defaults():
    cm = ConfigManager(profile_override=DeploymentProfile.JETSON)
    assert cm.get_setting("cuda_enabled") is True
    dict_repr = cm.to_dict()
    assert "profile_name" in dict_repr


def test_config_manager_get_runtime_mode():
    cm_sim = ConfigManager(profile_override=DeploymentProfile.SIMULATION)
    assert cm_sim.get_runtime_mode() == RuntimeMode.SIMULATION

    cm_laptop = ConfigManager(profile_override=DeploymentProfile.LAPTOP)
    assert cm_laptop.get_runtime_mode() == RuntimeMode.LAPTOP

    cm_pi = ConfigManager(profile_override=DeploymentProfile.RASPBERRY_PI)
    assert cm_pi.get_runtime_mode() == RuntimeMode.RASPBERRY_PI
