from deployment.configs.config_manager import ConfigManager, DeploymentProfile


def test_configuration_defaults():
    cm = ConfigManager(profile_override=DeploymentProfile.JETSON)
    assert cm.get_setting("cuda_enabled") is True
    dict_repr = cm.to_dict()
    assert "profile_name" in dict_repr
