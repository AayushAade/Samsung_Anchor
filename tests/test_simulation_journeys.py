"""
Every simulated journey passes, the runner reports failures, journeys are
isolated from each other and from the user's real data.
"""

from __future__ import annotations

import os

import pytest

from config import settings
from src.simulation.journeys import Journey, Step, all_journeys, run_journey, say
from src.simulation.battery import SimulatedBattery
from src.simulation.clock import SimulatedClock
from src.simulation.journeys import START


@pytest.mark.parametrize("journey", all_journeys(), ids=lambda j: j.name)
def test_journey(journey):
    result = run_journey(journey)
    assert result.passed, result.failures


def test_runner_reports_wrong_expectations_and_forbidden_claims():
    bad = run_journey(Journey("meta_bad", "", [say("What day is it?", expect="Saturday")]))
    assert not bad.passed and "expected 'Saturday'" in bad.failures[0]
    forbidden = run_journey(Journey("meta_forbid", "", [say("Hello", forbid="How can I help")]))
    assert not forbidden.passed


def test_journeys_restore_settings_and_clean_up():
    before = (settings.DB_PATH, settings.LOG_DIR)
    seen = {}

    def grab(ctx):
        seen["dir"] = ctx.dir
        return None
    run_journey(Journey("meta_iso", "", [Step("check", (grab, "grab dir")), say("I like tea")]))
    assert (settings.DB_PATH, settings.LOG_DIR) == before
    assert not os.path.exists(seen["dir"])


def test_battery_thresholds_and_drain():
    clock = SimulatedClock(START)
    b = SimulatedBattery(clock, level_pct=25, drain_pct_per_hour=10)
    assert b.reading().state == "OK" and b.notice() is None
    clock.advance(hours=1)
    assert b.reading().state == "LOW" and "15%" in b.notice()
    assert b.notice() is None  # once per threshold
    clock.advance(hours=1)
    assert b.reading().state == "CRITICAL" and "almost empty" in b.notice()
    b.set_charging(True)
    clock.advance(hours=1)
    assert b.reading().level_pct == 45.0 and b.reading().source == "SIMULATED_BATTERY"
