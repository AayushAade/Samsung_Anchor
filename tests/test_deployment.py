from deployment.configs.config_manager import ConfigManager, DeploymentProfile


def test_deployment_profile_loader():
    cm = ConfigManager(profile_override=DeploymentProfile.RASPBERRY_PI)
    assert cm.get_profile() == DeploymentProfile.RASPBERRY_PI
    assert cm.get_setting("target_fps") == 15.0
