from src.runtime.runtime_manager import RuntimeManager
from src.runtime.runtime_models import RuntimeMode


def test_runtime_manager_lifecycle():
    mgr = RuntimeManager()
    summary = mgr.get_runtime_summary()

    assert summary["mode"] == RuntimeMode.SIMULATION.value
    assert summary["connected_devices"] >= 5
    assert summary["cpu_usage_pct"] > 0
    assert summary["ram_usage_pct"] > 0

    mgr.shutdown_hardware()
