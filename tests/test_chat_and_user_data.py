"""
Text conversation mode and user data controls (view / correct / export / delete),
exercised through the real application factory and pipeline.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from src.application.chat import ChatSession
from src.application.factory import build_application
from src.memory import user_data
from src.memory.database import MemoraDatabase


def _session(path, confirm=lambda prompt: "DELETE", tmp_log=None):
    coord = build_application(live_hardware=False, database=MemoraDatabase(path))
    return ChatSession(coord, log_path=tmp_log, confirm=confirm)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "chat.sqlite")


@pytest.fixture
def log_path(tmp_path):
    return str(tmp_path / "chat.log")


def test_onboarding_conversation_and_restart(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    assert "What would you like me to call you" in s.opening()
    assert s.handle("My name is Sid").startswith("Nice to meet you, Sid")
    assert "remember" in s.handle("My daughter is Riya")
    s.close()

    s2 = _session(db_path, tmp_log=log_path)
    assert s2.opening() == "Welcome back, Sid. How can I help?"
    assert "Riya" in s2.handle("Who is my daughter?")
    s2.close()


def test_pipeline_diagnostics_go_to_log_not_conversation(db_path, log_path, capsys):
    s = _session(db_path, tmp_log=log_path)
    capsys.readouterr()
    reply = s.handle("I like green tea")
    out = capsys.readouterr().out
    assert reply == "I'll remember that you like green tea."
    assert "[DEBUG]" not in out and "Episode Logging" not in out
    assert os.path.getsize(log_path) > 0
    s.close()


def test_memories_listing_and_forget(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    s.handle("I like tea")
    s.handle("I like cricket")
    listing = s.handle("/memories")
    assert '1. "I like tea"' in listing and '2. "I like cricket"' in listing
    assert s.handle("/forget 1") == 'Deleted: "I like tea".'
    assert "tea" not in s.handle("What do I like?")
    assert s.handle("/forget 9").startswith("Please give the number")
    s.close()


def test_superseded_facts_are_marked_in_listing(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    s.handle("My daughter is Riya")
    s.handle("My daughter's name is Priya")
    listing = s.handle("/memories")
    assert "replaced by a newer statement" in listing
    s.close()


def test_export_contains_facts_and_is_private(db_path, log_path, tmp_path):
    s = _session(db_path, tmp_log=log_path)
    s.handle("My name is Sid")
    s.handle("I like jazz")
    out = tmp_path / "export.json"
    assert str(out) in s.handle(f"/export {out}")
    data = json.loads(out.read_text())
    assert data["preferred_name"] == "Sid"
    assert [f["statement"] for f in data["facts"]] == ["I like jazz"]
    assert "embedding" not in out.read_text().replace("Face embeddings are not exported", "")
    assert oct(os.stat(out).st_mode & 0o777) == "0o600"
    s.close()


def test_delete_all_requires_confirmation_and_removes_everything(db_path, log_path):
    s = _session(db_path, confirm=lambda p: "no", tmp_log=log_path)
    s.handle("I like jazz")
    assert s.handle("/delete-all") == "Cancelled. Nothing was deleted."
    assert user_data.list_facts(s.db)

    s.confirm = lambda p: "DELETE"
    s.db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    s.db.log_object("keys", 0, 0, "Hall")
    assert s.handle("/delete-all") == "All your data has been deleted."
    s.close()

    reopened = MemoraDatabase(db_path)
    assert user_data.list_facts(reopened) == []
    assert user_data.list_people(reopened) == []
    assert user_data.list_objects(reopened) == []
    assert len(reopened.vector_store) == 0
    assert reopened.check_integrity()["ok"]


def test_status_states_sensors_off_and_db_path(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    status = s.handle("/status")
    assert "Camera: off" in status and "Microphone: off" in status
    assert "chat_v2.sqlite" in status or "chat.sqlite" in status
    s.close()


def test_quit_and_unknown_command(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    assert s.handle("/quit") is None
    assert "Type /help" in s.handle("/frobnicate")
    s.close()


def test_run_loop_end_to_end(db_path, log_path):
    s = _session(db_path, tmp_log=log_path)
    inputs = iter(["My name is Ana", "What time is it?", "/quit"])
    outputs = []
    s.run(read=lambda prompt: next(inputs), write=outputs.append)
    text = "\n".join(outputs)
    assert "Nice to meet you, Ana" in text
    assert "MEMORA: It's" in text
    assert text.endswith("MEMORA: Goodbye.")
