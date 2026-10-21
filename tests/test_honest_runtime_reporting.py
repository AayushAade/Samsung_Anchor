"""
Runtime status and telemetry must reflect what was actually checked or measured.
"""

from __future__ import annotations

from src.application.factory import build_application
from src.memory.database import MemoraDatabase
from src.runtime.runtime import AnchorRuntime


class CountingSpeaker:
    def __init__(self):
        self.executed = 0

    def execute(self, action):
        self.executed += 1


def _runtime(db=None, speaker=None):
    coord = build_application(live_hardware=False, database=db or MemoraDatabase(":memory:"), speaker=speaker)
    rt = AnchorRuntime(coord)
    rt.initialize()
    return coord, rt


def test_simulated_devices_never_reported_ready():
    _, rt = _runtime()
    statuses = rt.get_subsystem_statuses()
    for name in ("Camera", "Audio", "Speaker", "Speech Recognition", "Perception"):
        assert "Simulated" in statuses[name], (name, statuses[name])


def test_memory_status_reflects_integrity(tmp_path):
    import numpy as np, os
    from src.memory.database import vector_store_paths
    path = str(tmp_path / "s.sqlite")
    db = MemoraDatabase(path)
    db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    os.remove(vector_store_paths(db.db_path)[1])
    _, rt = _runtime(MemoraDatabase(path))
    assert rt.get_subsystem_statuses()["Memory"].startswith("WARNING (1 identities lack face embeddings")


def test_runtime_loop_does_not_speak_actions_a_second_time():
    speaker = CountingSpeaker()
    coord, rt = _runtime(speaker=speaker)
    coord.pipeline.process(user_speech="Hello")  # pipeline already spoke via the speaker HAL
    rt.run_continuous(max_cycles=2, cycle_delay=0)
    assert speaker.executed == 0


def test_diagnostic_report_has_no_unconditional_ready_claims():
    coord, _ = _runtime()
    report = coord.pipeline.runtime_manager.generate_diagnostic_report()
    assert "Google ASR" not in report
    assert "gemini-1.5" not in report
    assert "SIMULATED" in report


def test_audit_outcome_reflects_speech_result():
    coord, _ = _runtime()
    coord.pipeline.process(user_speech="Hello")
    assert coord.pipeline.last_speech_delivered is True


def test_audit_final_action_is_what_was_actually_done():
    coord, _ = _runtime()
    coord.pipeline.process(user_speech="Hello")
    assert coord.pipeline.latest_audit_record.final_action == "SPEAK"
    coord.pipeline.process(user_speech="I can't breathe")
    assert coord.pipeline.latest_audit_record.final_action == "ESCALATE"
