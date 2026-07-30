from deployment.metrics.metrics_collector import MetricsCollector


def test_metrics_collector_counters():
    mc = MetricsCollector()
    mc.record_cycle(32.5)
    mc.record_perception_event()
    mc.record_error()

    summary = mc.get_metrics_summary()
    assert summary["total_cycles"] == 1
    assert summary["last_latency_ms"] == 32.5
    assert summary["perception_events"] == 1
    assert summary["errors_count"] == 1
