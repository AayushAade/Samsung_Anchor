import os
from enum import Enum
from typing import Any, Dict
from src.runtime.runtime_models import RuntimeMode


class DeploymentProfile(Enum):
    DEV = "Development"
    SIMULATION = "Simulation"
    LAPTOP = "Laptop"
    RASPBERRY_PI = "Raspberry Pi"
    JETSON = "NVIDIA Jetson"
    PRODUCTION = "Production Edge"


class ConfigManager:
    """
    Environment-based configuration profile manager.
    Supports DEV, SIMULATION, LAPTOP, RASPBERRY_PI, JETSON, and PRODUCTION profiles.
    """

    def __init__(self, profile_override: DeploymentProfile = None) -> None:
        if profile_override:
            self._profile = profile_override
        else:
            env_val = os.getenv("MEMORA_PROFILE", "SIMULATION").upper()
            try:
                self._profile = DeploymentProfile[env_val]
            except KeyError:
                self._profile = DeploymentProfile.SIMULATION

        self._settings = self._load_defaults(self._profile)

    def _load_defaults(self, profile: DeploymentProfile) -> Dict[str, Any]:
        base_config = {
            "profile_name": profile.value,
            "target_fps": 30.0,
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "enable_telemetry": True,
            "max_memory_mb": 2048,
            "dashboard_port": 8000,
        }

        if profile == DeploymentProfile.DEV:
            base_config["log_level"] = "DEBUG"
            base_config["dashboard_port"] = 8000
        elif profile == DeploymentProfile.SIMULATION:
            base_config["target_fps"] = 30.0
            base_config["simulation_mode"] = True
        elif profile == DeploymentProfile.RASPBERRY_PI:
            base_config["target_fps"] = 15.0
            base_config["max_memory_mb"] = 1024
        elif profile == DeploymentProfile.JETSON:
            base_config["target_fps"] = 60.0
            base_config["cuda_enabled"] = True
        elif profile == DeploymentProfile.PRODUCTION:
            base_config["log_level"] = "WARNING"
            base_config["telemetry_interval_sec"] = 5

        return base_config

    def get_profile(self) -> DeploymentProfile:
        return self._profile

    def get_runtime_mode(self) -> RuntimeMode:
        profile_map = {
            DeploymentProfile.DEV: RuntimeMode.LAPTOP,
            DeploymentProfile.SIMULATION: RuntimeMode.SIMULATION,
            DeploymentProfile.LAPTOP: RuntimeMode.LAPTOP,
            DeploymentProfile.RASPBERRY_PI: RuntimeMode.RASPBERRY_PI,
            DeploymentProfile.JETSON: RuntimeMode.JETSON,
            DeploymentProfile.PRODUCTION: RuntimeMode.PRODUCTION,
        }
        return profile_map.get(self._profile, RuntimeMode.SIMULATION)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._settings)
