from src.runtime.runtime_models import HealthMetrics


def test_runtime_health_metrics():
    metrics = HealthMetrics(
        cpu_usage_pct=14.5,
        ram_usage_pct=38.2,
        camera_fps=30.0,
        audio_latency_ms=12.1,
        connected_devices_count=6,
    )

    assert metrics.cpu_usage_pct == 14.5
    assert metrics.camera_fps == 30.0
    assert metrics.connected_devices_count == 6
