"""
Deterministic, step-based simulation of complete user journeys.

Each journey runs in its own temporary directory (database, logs, exports,
backups) with a SimulatedClock, through the same ChatSession and pipeline a
person uses. Steps assert what must appear in MEMORA's reply and what must
never appear. One journey's state can never reach another's, and the user's
real database and logs are never touched.

Run: python app.py --simulate [JOURNEY_NAME ...]
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from src.simulation.battery import SimulatedBattery
from src.simulation.clock import SimulatedClock

START = datetime(2026, 3, 10, 9, 0)  # a Tuesday morning

# Claims MEMORA must never make in any simulated journey.
GLOBAL_FORBIDDEN = ["I've called", "I have called", "has been notified", "have been notified",
                    "help is on the way", "Eleanor", "Sarah Jenkins", "Donepezil", "Traceback"]


@dataclass
class Step:
    kind: str
    arg: Any = None
    expect: tuple = ()
    forbid: tuple = ()


def say(text, expect=(), forbid=()):
    return Step("say", text, tuple([expect] if isinstance(expect, str) else expect),
                tuple([forbid] if isinstance(forbid, str) else forbid))


def check(fn: Callable[["JourneyContext"], Optional[str]], label: str):
    """fn returns None if the check passes, else a failure description."""
    return Step("check", (fn, label))


@dataclass
class Journey:
    name: str
    description: str
    steps: list
    consent: bool = True        # grant conversation-storage consent up front
    battery: bool = False       # attach a SimulatedBattery


@dataclass
class JourneyResult:
    name: str
    passed: bool
    steps_run: int
    failures: list = field(default_factory=list)
    transcript: list = field(default_factory=list)
    seconds: float = 0.0


class JourneyContext:
    """Isolated environment for one journey."""

    def __init__(self, journey: Journey) -> None:
        from config import settings
        self.dir = tempfile.mkdtemp(prefix=f"memora-sim-{journey.name}-")
        self.db_path = os.path.join(self.dir, "memora.sqlite")
        self.log_dir = os.path.join(self.dir, "logs")
        os.makedirs(self.log_dir)
        self._saved_settings = (settings.DB_PATH, settings.LOG_DIR)
        settings.DB_PATH, settings.LOG_DIR = self.db_path, self.log_dir
        self.clock = SimulatedClock(START)
        self.journey = journey
        self.battery = SimulatedBattery(self.clock, level_pct=60) if journey.battery else None
        self.session = None
        self.last_reply = ""
        self.open()
        if journey.consent:
            from src.clinical.clinical_models import ConsentFeature
            self.session.pipeline.consent_mgr.update_consent(ConsentFeature.CONVERSATION_STORAGE, True)

    # -- lifecycle ---------------------------------------------------------
    def open(self) -> None:
        from src.application.chat import ChatSession
        from src.application.factory import build_application
        from src.memory.database import MemoraDatabase
        with contextlib.redirect_stdout(io.StringIO()):
            coord = build_application(live_hardware=False, database=MemoraDatabase(self.db_path))
        coord.pipeline.set_clock(self.clock)
        coord.pipeline.battery = self.battery
        self.session = ChatSession(coord, log_path=os.path.join(self.log_dir, "chat_debug.log"),
                                   confirm=lambda prompt: "DELETE")

    def restart(self) -> None:
        if self.session is not None:
            self.session.close()
        self.open()

    def close(self) -> None:
        from config import settings
        try:
            if self.session is not None:
                self.session.close()
        finally:
            settings.DB_PATH, settings.LOG_DIR = self._saved_settings
            shutil.rmtree(self.dir, ignore_errors=True)

    # -- helpers used by steps --------------------------------------------
    @property
    def pipeline(self):
        return self.session.pipeline

    @property
    def db(self):
        return self.session.db

    def presence(self, face_id: Optional[str], name: Optional[str], relationship: Optional[str]) -> str:
        """A synthetic perception event (source SIMULATED_PERCEPTION) through the real pipeline."""
        self.pipeline.reset()
        with contextlib.redirect_stdout(io.StringIO()):
            actions = self.pipeline.process({"face_id": face_id, "name": name, "relationship": relationship,
                                             "source": "SIMULATED_PERCEPTION"})
        return " ".join(a.message for a in actions if getattr(a, "message", None))

    def observe(self, obj: str, room: str) -> None:
        self.db.log_object(obj, 0.0, 0.0, room, source="SIMULATED_CAMERA", when=self.clock())


def _run_step(ctx: JourneyContext, step: Step) -> tuple[str, list]:
    failures = []
    reply = ""
    if step.kind == "say":
        # "__DIR__" lets a step refer to the journey's own temporary directory.
        reply = ctx.session.handle(step.arg.replace("__DIR__", ctx.dir)) or ""
    elif step.kind == "opening":
        reply = ctx.session.opening()
    elif step.kind == "advance":
        ctx.clock.advance(minutes=step.arg)
    elif step.kind == "restart":
        ctx.restart()
    elif step.kind == "presence":
        reply = ctx.presence(*step.arg)
    elif step.kind == "observe":
        ctx.observe(*step.arg)
    elif step.kind == "battery":
        level, charging = step.arg
        ctx.battery.set_level(level)
        ctx.battery.set_charging(charging)
    elif step.kind == "fail":
        getattr(ctx.pipeline.runtime_manager, step.arg).inject_failure()
    elif step.kind == "status":
        from src.runtime.runtime import AnchorRuntime
        reply = "; ".join(f"{k}: {v}" for k, v in AnchorRuntime(ctx.session.coordinator).get_subsystem_statuses().items())
    elif step.kind == "check":
        fn, label = step.arg
        problem = fn(ctx)
        if problem:
            failures.append(f"check '{label}': {problem}")
    else:
        failures.append(f"unknown step kind {step.kind}")
    ctx.last_reply = reply
    lowered = reply.lower()
    for e in step.expect:
        if e.lower() not in lowered:
            failures.append(f"{step.kind} {step.arg!r}: expected {e!r} in reply {reply!r}")
    for f in tuple(step.forbid) + tuple(GLOBAL_FORBIDDEN):
        if f.lower() in lowered:
            failures.append(f"{step.kind} {step.arg!r}: forbidden {f!r} in reply {reply!r}")
    return reply, failures


def run_journey(journey: Journey) -> JourneyResult:
    t0 = time.perf_counter()
    result = JourneyResult(journey.name, True, 0)
    ctx = None
    try:
        ctx = JourneyContext(journey)
        for step in journey.steps:
            reply, failures = _run_step(ctx, step)
            result.steps_run += 1
            if step.kind in ("say", "opening", "presence", "status"):
                result.transcript.append((step.kind, str(step.arg), reply))
            if failures:
                result.failures.extend(failures)
                break
    except Exception as e:  # a crash is a failed journey, reported, never hidden
        result.failures.append(f"exception: {type(e).__name__}: {e}")
    finally:
        if ctx is not None:
            ctx.close()
    result.passed = not result.failures
    result.seconds = round(time.perf_counter() - t0, 2)
    return result


# ----------------------------------------------------------------------------
# Journey catalogue
# ----------------------------------------------------------------------------

def _nothing_personal_stored(ctx) -> Optional[str]:
    import sqlite3
    con = sqlite3.connect(ctx.db.db_path)
    try:
        tables = ["relevant_memories", "episodes", "objects", "identities", "care_items", "care_events",
                  "semantic_nodes", "identity_evidence"]
        stored = {t: n for t in tables if (n := con.execute(f'select count(*) from "{t}"').fetchone()[0])}
        keys = {r[0] for r in con.execute("select key from system_state")}
    finally:
        con.close()
    extra = keys - {"current_room", "next_anon_index", "schema_version", "consent:CONVERSATION_STORAGE"}
    return None if not stored and not extra else f"stored {stored} keys {extra}"


def _facts(ctx):
    from src.memory import user_data
    return user_data.list_facts(ctx.db)


def all_journeys() -> list[Journey]:
    J = Journey
    return [
        J("first_time_onboarding", "Consent question, then name, then greeting by name after restart", consent=False, steps=[
            Step("opening", expect=("may I save what you tell me",)),
            say("My name is Ana", expect="Please answer yes or no first"),
            say("yes", expect="What would you like me to call you"),
            say("My name is Ana", expect="Nice to meet you, Ana"),
            Step("restart"),
            Step("opening", expect=("Welcome back, Ana",)),
        ]),
        J("consent_declined", "Declining storage: nothing saved, honest replies", consent=False, steps=[
            Step("opening"),
            say("no", expect="won't save anything"),
            say("My daughter is Riya", expect="memory is turned off", forbid="I'll remember"),
            say("/add-medication Aspirin at 08:00", expect="memory is turned off", forbid="Saved"),
            say("/set-trusted-contact Riya 555-0100", expect="memory is turned off", forbid="Saved"),
            say("I took my pills", expect="haven't recorded it", forbid="noted"),
            say("What day is it?", expect="Tuesday, March 10"),
            check(lambda c: _nothing_personal_stored(c), "nothing stored"),
        ]),
        J("facts_create_correct_recall_delete", "Fact lifecycle with history", steps=[
            say("I like green tea", expect="I'll remember that you like green tea"),
            say("What tea do I like?", expect="You told me today that you like green tea"),
            say("I don't like green tea anymore", expect="I've updated that"),
            say("Do I like green tea?", expect="don't like green tea"),
            say("/memories", expect=("replaced by a newer statement",)),
            say("/forget 1", expect="Deleted"),
            check(lambda c: None if len(_facts(c)) == 1 else f"expected 1 fact, have {len(_facts(c))}", "one fact left"),
        ]),
        J("unknown_and_ambiguous", "Unknown answers are honest; pronouns are not guessed", steps=[
            say("Who is my son?", expect="I don't know who your son is yet"),
            say("What is my favourite song?", expect="haven't told me your favorite song"),
            say("I like it", expect="What do you mean by 'it'"),
            say("Have you seen them?", expect="Which item do you mean"),
            say("Is it raining?", expect="not sure I understood"),
        ]),
        J("conflicting_memories", "Two daughters are surfaced, a correction retracts one", steps=[
            say("My daughter is Riya"),
            say("My daughter is Priya", expect="more than one daughter"),
            say("Who is my daughter?", expect=("Riya", "Priya")),
            say("My daughter is not Riya", expect="won't say your daughter is Riya"),
            say("Who is my daughter?", expect="Priya", forbid="daughter is Riya"),
        ]),
        J("names_and_time", "Statements are not names; time comes from the clock", steps=[
            say("I am tired today", expect="rest", forbid="Nice to meet you"),
            say("What's my name?", expect="haven't told me your name"),
            say("Call me Nani", expect="Nice to meet you, Nani"),
            say("What time is it?", expect="9:00 AM"),
            Step("advance", 30),
            say("What time is it?", expect="9:30 AM"),
            say("What year is it?", expect="2026"),
        ]),
        J("known_visitor", "A named visitor is announced by name and relationship", steps=[
            Step("presence", ("face_2", "Riya", "Daughter"), expect=("Your daughter, Riya, is here",)),
            say("Who visited today?", expect="I recorded Riya today"),
        ]),
        J("unknown_visitor", "An unrecognised face is never given a name", steps=[
            Step("presence", ("face_9", None, None), forbid=("Riya", "Your daughter")),
            say("Who visited today?", expect="haven't recorded any visitors"),
        ]),
        J("self_is_not_a_visitor", "The person's own turns are not visits", steps=[
            say("My name is Ana"),
            say("I like tea"),
            say("Who visited today?", expect="haven't recorded any visitors"),
        ]),
        J("simulated_object_observation", "Simulated sightings are labelled as such", steps=[
            Step("observe", ("keys", "Hall")),
            Step("advance", 20),
            say("Where are my keys?", expect=("in the Hall", "about 20 minutes ago", "simulation")),
        ]),
        J("stale_object_observation", "Old sightings are not current-location claims", steps=[
            Step("observe", ("glasses", "Kitchen")),
            Step("advance", 60 * 26),
            say("Where are my glasses?", expect=("yesterday", "may have been moved")),
            say("Where is my wallet?", expect="haven't seen your wallet"),
        ]),
        J("battery_low_and_critical", "Simulated battery notices, once per threshold", battery=True, steps=[
            Step("battery", (18, False)),
            say("Hello", expect="battery is getting low (18%, simulated)"),
            say("What day is it?", forbid="battery"),
            Step("battery", (4, False)),
            say("Hello", expect=("almost empty (4%, simulated)", "is saved")),
            Step("status", expect=("Battery: WARNING (Simulated, 4%, CRITICAL",)),
            Step("battery", (50, True)),
            say("Hello", forbid="battery"),
        ]),
        J("sensor_unavailable", "Failed simulated sensors are reported, not hidden", steps=[
            Step("fail", "camera"),
            Step("fail", "speaker"),
            Step("status", expect=("Camera: FAILED", "Speaker: FAILED")),
            say("What day is it?", expect="Tuesday"),
            check(lambda c: None if c.pipeline.last_speech_delivered is False else "speech reported delivered",
                  "speaker failure recorded"),
        ]),
        J("restart_persistence", "Facts, name and schedules survive restart", steps=[
            say("My name is Ana"),
            say("My son is Leo"),
            say("/add-medication Aspirin at 20:00"),
            Step("restart"),
            say("Who is my son?", expect="Leo"),
            say("/medications", expect="Aspirin"),
            Step("opening", expect=("Welcome back, Ana",)),
        ]),
        J("reminders_and_throttling", "Reminders when overdue, at most once per interval, stop after a report", steps=[
            say("/add-medication Aspirin at 09:15"),
            say("Hello", forbid="reminder"),
            Step("advance", 50),
            say("Hello", expect=("gentle reminder", "Aspirin")),
            say("What day is it?", forbid="reminder"),
            say("I took my aspirin", expect="you told me you took your Aspirin"),
            Step("advance", 120),
            say("Hello", forbid="reminder"),
            say("Did I take my medicine?", expect=("told me today that you took your Aspirin", "only go by what you tell me")),
        ]),
        J("urgent_distress", "Urgent statements get human-help guidance and no false claims", steps=[
            say("/set-emergency-number 112"),
            say("/set-trusted-contact Riya 555-0100"),
            say("Help me, I fell and can't get up", expect=("call 112", "Riya on 555-0100", "can't contact anyone myself")),
            say("I can't breathe", expect="call 112"),
            say("Did you call my daughter?", expect="haven't contacted anyone"),
            say("I fell asleep in my chair", forbid=("call 112", "emergency")),
        ]),
        J("medical_boundaries", "No medication advice or diagnosis", steps=[
            say("Should I take an extra pill?", expect="can't give advice about medicines"),
            say("Do I have dementia?", expect="can't tell whether you're unwell"),
        ]),
        J("export_and_delete", "Export contains the data; delete-all removes it", steps=[
            say("My name is Ana"),
            say("I like jazz"),
            say("/export __DIR__/export.json", expect="Saved a copy"),
            say("/delete-all", expect="All your data has been deleted"),
            say("/memories", expect="haven't told me anything"),
            check(lambda c: None if c.db.episode_repo.count() == 0 else "episodes remain", "no episodes left"),
        ]),
        J("backup_and_corruption_recovery", "Damaged database is recovered from a verified backup", steps=[
            say("My son is Leo"),
            check(lambda c: _backup(c), "backup written"),
            check(lambda c: _corrupt_and_restore(c), "restore after corruption"),
            Step("restart"),
            say("Who is my son?", expect="Leo"),
        ]),
        J("extended_operation", "300 simulated turns over 3 simulated days stay stable", steps=[
            check(lambda c: _extended(c, 300), "stable over 300 turns"),
        ]),
    ]


def _backup(ctx) -> Optional[str]:
    from src.memory.backup import create_backup, verify_backup
    ctx.backup_dir = create_backup(ctx.db.db_path, os.path.join(ctx.dir, "backups"))
    return None if verify_backup(ctx.backup_dir)["integrity"]["ok"] else "backup integrity check failed"


def _corrupt_and_restore(ctx) -> Optional[str]:
    from src.memory.backup import restore_backup
    from src.memory.database import DatabaseUnavailableError, open_user_database
    path = ctx.db.db_path
    ctx.session.close()
    with open(path, "wb") as f:
        f.write(b"garbage that is not sqlite")
    try:
        open_user_database(path)
        return "corrupt database was opened without error"
    except DatabaseUnavailableError:
        pass
    restore_backup(ctx.backup_dir, path)
    ctx.session = None
    return None


def _extended(ctx, turns: int) -> Optional[str]:
    import threading
    utterances = ["What time is it?", "I like tea", "Where are my keys?", "Who is my son?", "Hello",
                  "What did I do today?", "Do I like tea?"]
    for warm in utterances:  # thread pools start lazily; measure after warm-up
        ctx.session.handle(warm)
    threads_before = threading.active_count()
    latencies = []
    for i in range(turns):
        t0 = time.perf_counter()
        reply = ctx.session.handle(utterances[i % len(utterances)])
        latencies.append(time.perf_counter() - t0)
        if not reply or "went wrong" in reply:
            return f"turn {i} failed: {reply!r}"
        ctx.clock.advance(minutes=15)
    if threading.active_count() > threads_before:
        return f"thread growth {threads_before} -> {threading.active_count()}"
    for _ in range(3):
        ctx.restart()
        ctx.session.handle("Hello")
    if threading.active_count() > threads_before:
        return f"threads leaked across restarts: {threads_before} -> {threading.active_count()}"
    first, last = sorted(latencies[:50])[25], sorted(latencies[-50:])[25]
    if last > max(0.05, first * 5):
        return f"median latency grew from {first*1000:.1f} ms to {last*1000:.1f} ms"
    return None


def run_all(names: Optional[list] = None) -> list[JourneyResult]:
    journeys = all_journeys()
    if names:
        unknown = set(names) - {j.name for j in journeys}
        if unknown:
            raise ValueError(f"Unknown journeys: {', '.join(sorted(unknown))}")
        journeys = [j for j in journeys if j.name in names]
    return [run_journey(j) for j in journeys]


def print_report(results: list[JourneyResult]) -> int:
    print("=" * 72)
    print("MEMORA SIMULATED JOURNEYS (synthetic data, simulated clock and sensors)")
    print("=" * 72)
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'}  {r.name:<36} {r.steps_run:>3} steps  {r.seconds:>6.2f}s")
        for f in r.failures:
            print(f"      - {f}")
    passed = sum(r.passed for r in results)
    print("-" * 72)
    print(f"{passed}/{len(results)} journeys passed. These are simulated software checks, "
          "not evidence of real-world or clinical effectiveness.")
    return 0 if passed == len(results) else 1
