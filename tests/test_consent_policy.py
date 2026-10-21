"""
Consent policy (docs/PRIVACY_AND_CONSENT.md), verified against persisted state.

If the person declines storage, no personal record of any kind may be written —
not through conversation, not through slash commands, not through identity
learning, not into logs. Only the consent decision itself and non-personal
system defaults may exist.
"""

from __future__ import annotations

import os
import sqlite3

import pytest

from src.application.chat import ChatSession
from src.application.factory import build_application
from src.clinical.consent_manager import ConsentRequiredError
from src.memory.database import MemoraDatabase

TOKEN = "zephyrine"  # marker that must never reach disk when storage is declined

PERSONAL_TABLES = ["relevant_memories", "episodes", "objects", "object_history", "identities",
                   "identity_evidence", "semantic_nodes", "care_items", "care_events",
                   "interaction_records", "feedback_events"]
NON_PERSONAL_STATE = {"current_room", "next_anon_index", "schema_version", "consent:CONVERSATION_STORAGE"}


def _session(tmp_path, answer):
    db = MemoraDatabase(str(tmp_path / "c.sqlite"))
    coord = build_application(live_hardware=False, database=db)
    s = ChatSession(coord, log_path=str(tmp_path / "logs" / "chat_debug.log"), confirm=lambda p: "DELETE")
    s.opening()
    s.handle(answer)
    return s


def _counts(db_path):
    con = sqlite3.connect(db_path)
    try:
        return {t: con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in PERSONAL_TABLES}
    finally:
        con.close()


def _state_keys(db_path):
    con = sqlite3.connect(db_path)
    try:
        return {r[0] for r in con.execute("select key from system_state")}
    finally:
        con.close()


ATTEMPTS = [
    f"My name is {TOKEN.capitalize()}",
    f"My daughter is {TOKEN}",
    f"I like {TOKEN} tea",
    f"/add-medication {TOKEN}pill at 00:01",
    f"/add-appointment {TOKEN} clinic on 2030-01-01 10:00",
    "/set-emergency-number 112",
    f"/set-trusted-contact {TOKEN} 555-0100",
    f"I took my {TOKEN}pill",
    "I took my pills",
    f"Where are my {TOKEN} keys?",
]


def test_declined_storage_writes_nothing_personal_anywhere(tmp_path):
    s = _session(tmp_path, "no")
    replies = [s.handle(a) for a in ATTEMPTS]
    db_path = s.db.db_path
    s.close()

    assert all(v == 0 for v in _counts(db_path).values()), _counts(db_path)
    assert _state_keys(db_path) <= NON_PERSONAL_STATE, _state_keys(db_path)
    for root, _, files in os.walk(tmp_path):
        for name in files:
            data = open(os.path.join(root, name), "rb").read()
            assert TOKEN.encode() not in data, f"{TOKEN} written to {name}"
    # Commands are refused with an explanation rather than claiming success.
    for reply in replies[3:7]:
        assert "memory is turned off" in reply and "Saved" not in reply
    assert "memory is turned off" in replies[8] and "noted" not in replies[8]


def test_allowed_storage_writes_each_record_type(tmp_path):
    s = _session(tmp_path, "yes")
    for a in ATTEMPTS[:8]:
        s.handle(a)
    db_path = s.db.db_path
    s.close()
    c = _counts(db_path)
    assert c["relevant_memories"] >= 2 and c["care_items"] == 2 and c["care_events"] == 1 and c["episodes"] >= 1
    assert {"user_preferred_name", "emergency_number", "trusted_contact"} <= _state_keys(db_path)


def test_revoking_consent_stops_new_writes_but_keeps_existing(tmp_path):
    s = _session(tmp_path, "yes")
    s.handle("I like green tea")
    assert "use /delete-all" in s.handle("/consent memory off")
    s.handle("I like coffee")
    s.handle("/add-medication Aspirin at 08:00")
    from src.memory import user_data
    assert [f["statement"] for f in user_data.list_facts(s.db)] == ["I like green tea"]
    assert user_data.export_user_data(s.db)["care_items"] == []
    # Deletion is always allowed, whatever the consent state.
    assert s.handle("/forget 1").startswith("Deleted")
    s.close()


def test_storage_layer_refuses_writes_without_consent(tmp_path):
    """Defence in depth: a bypass of the user-facing checks raises instead of writing."""
    coord = build_application(live_hardware=False, database=MemoraDatabase(str(tmp_path / "d.sqlite")))
    p = coord.pipeline
    with pytest.raises(ConsentRequiredError):
        p.medication_mgr.add_scheduled("X", "08:00")
    with pytest.raises(ConsentRequiredError):
        p.appointment_mgr.add_scheduled("X", __import__("datetime").datetime(2030, 1, 1))
    with pytest.raises(ConsentRequiredError):
        p.conversational_memory._save_fact("f1", "likes:x", "x", "positive", "I like x")
    assert all(v == 0 for v in _counts(coord.database.db_path).values())


def test_identity_learning_requires_storage_consent(tmp_path):
    from src.clinical.clinical_models import ConsentFeature
    coord = build_application(live_hardware=False, database=MemoraDatabase(str(tmp_path / "e.sqlite")))
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.FACE_RECOGNITION, True)
    assert coord.start_identity_learning("face_1") is False      # memory consent missing
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.CONVERSATION_STORAGE, True)
    assert coord.start_identity_learning("face_1") is True


def test_identity_evidence_needs_consent_at_the_storage_layer(tmp_path):
    """Every caller (coordinator.process_transcript, services, demos) is covered, not just async learning."""
    from src.clinical.clinical_models import ConsentFeature
    coord = build_application(live_hardware=False, database=MemoraDatabase(str(tmp_path / "f.sqlite")))
    db = coord.database
    with pytest.raises(ConsentRequiredError):
        db.add_evidence("face_1", "Bob", "Son", f"I'm Bob, {TOKEN}")
    result = coord.process_transcript("face_1", f"Hi, I'm Bob, your son. {TOKEN}")
    assert result == {"success": False, "reason": "Consent required"}
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.CONVERSATION_STORAGE, True)
    with pytest.raises(ConsentRequiredError):            # faces consent still missing
        db.add_evidence("face_1", "Bob", "Son", "I'm Bob")
    assert _counts(db.db_path)["identity_evidence"] == 0
    assert TOKEN.encode() not in open(db.db_path, "rb").read()
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.FACE_RECOGNITION, True)
    import numpy as np
    face = db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    assert coord.process_transcript(face, "Hi, I'm Bob, your son.")["success"] is True
    assert _counts(db.db_path)["identity_evidence"] == 1


def test_export_contains_every_stored_personal_row(tmp_path):
    """Found in review: identity evidence (transcripts), derived knowledge and consent decisions were not exported."""
    import json
    import numpy as np
    from src.clinical.clinical_models import ConsentFeature
    from src.memory import user_data
    s = _session(tmp_path, "yes")
    for a in ATTEMPTS[:8]:
        s.handle(a)
    coord = s.coordinator
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.FACE_RECOGNITION, True)
    face = s.db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    coord.process_transcript(face, f"Hi, I'm Bob, your son. {TOKEN}-intro")
    out = tmp_path / "export.json"
    user_data.write_export(s.db, str(out))
    data = json.loads(out.read_text())
    counts = _counts(s.db.db_path)
    s.close()
    assert {t: len(data["all_records"][t]) for t in PERSONAL_TABLES} == counts
    assert counts["identity_evidence"] == 1 and f"{TOKEN}-intro" in out.read_text()
    assert data["consent_decisions"]["CONVERSATION_STORAGE"].startswith("granted")
