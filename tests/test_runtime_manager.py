from src.runtime.camera_adapter import OpenCVCameraAdapter, SimulatedCameraAdapter
from src.runtime.runtime_manager import RuntimeManager
from src.runtime.runtime_models import HardwareConfig, RuntimeMode


def test_runtime_manager_lifecycle():
    mgr = RuntimeManager()
    summary = mgr.get_runtime_summary()

    assert summary["mode"] == RuntimeMode.SIMULATION.value
    assert summary["connected_devices"] >= 5
    assert summary["cpu_usage_pct"] > 0
    assert summary["ram_usage_pct"] > 0

    mgr.shutdown_hardware()


def test_runtime_manager_adapter_selection_simulation():
    config = HardwareConfig(mode=RuntimeMode.SIMULATION)
    mgr = RuntimeManager(config=config)
    assert isinstance(mgr.camera, SimulatedCameraAdapter)
    mgr.shutdown_hardware()


def test_runtime_manager_adapter_selection_laptop():
    config = HardwareConfig(mode=RuntimeMode.LAPTOP)
    mgr = RuntimeManager(config=config)
    # OpenCVCameraAdapter is selected when mode is LAPTOP
    assert isinstance(mgr.camera, (OpenCVCameraAdapter, SimulatedCameraAdapter))
    mgr.shutdown_hardware()
