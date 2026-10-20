"""
Storage failures produce actionable messages without touching data, and
/delete-all also removes logs and in-memory session state.
"""

from __future__ import annotations

import os
import subprocess
import sys

from src.application.chat import ChatSession
from src.application.factory import build_application
from src.memory.database import DatabaseUnavailableError, MemoraDatabase, open_user_database
from tests.consent_helpers import allow_memory

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_chat(db_path, stdin="/quit\n"):
    env = dict(os.environ, MEMORA_DB_PATH=db_path)
    return subprocess.run([sys.executable, "app.py", "--chat"], cwd=REPO, input=stdin, env=env,
                          capture_output=True, text=True, timeout=120)


def test_corrupt_database_is_reported_and_left_untouched(tmp_path):
    bad = tmp_path / "bad.sqlite"
    bad.write_text("this is not a database")
    r = _run_chat(str(bad))
    assert r.returncode == 2
    assert "could not open its memory file" in r.stdout and "Nothing was changed" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr
    assert bad.read_text() == "this is not a database"


def test_unwritable_location_is_reported(tmp_path):
    ro = tmp_path / "ro"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        try:
            open_user_database(str(ro / "x.sqlite"))
            raised = False
        except DatabaseUnavailableError as e:
            raised = "MEMORA_DB_PATH" in str(e)
    finally:
        ro.chmod(0o700)
    assert raised


def test_delete_all_removes_logs_and_session_state(tmp_path):
    db = MemoraDatabase(str(tmp_path / "d.sqlite"))
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "memora.log").write_text("User said: I like tea")
    (log_dir / "memora.log.1").write_text("old")
    (log_dir / "unrelated.txt").write_text("keep me")
    coord = build_application(live_hardware=False, database=db)
    allow_memory(coord.pipeline)
    s = ChatSession(coord, log_path=str(log_dir / "chat_debug.log"), confirm=lambda p: "DELETE")
    s.handle("I like tea")
    s.handle("Where are my keys?")
    reply = s.handle("/delete-all")
    assert reply.startswith("All your data has been deleted, including 3 log file(s)")
    assert "Backup copies" in reply
    assert not (log_dir / "memora.log").exists() and not (log_dir / "memora.log.1").exists()
    assert (log_dir / "unrelated.txt").read_text() == "keep me"
    assert s.pipeline.conversational_memory.search_history == []
    assert "may I save" in s.opening()  # consent was reset; the next session asks again
