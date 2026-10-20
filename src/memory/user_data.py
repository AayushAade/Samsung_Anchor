"""
User data controls: view, export, and delete what MEMORA has stored.

Deletion removes rows from SQLite and, for people, their face embeddings from
the vector store, then verifies the result rather than assuming success.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from src.cognition.conversational_memory import ConversationalMemory, PREFERRED_NAME_KEY
from src.memory.models import (EpisodeModel, FeedbackEventModel, Identity, IdentityEvidence,
                               InteractionRecordModel, Object, ObjectHistory, RelevantMemoryModel,
                               SemanticNodeModel, SystemState)

# Child tables first so foreign keys are never left dangling.
PERSONAL_TABLES = (FeedbackEventModel, InteractionRecordModel, RelevantMemoryModel, EpisodeModel,
                   ObjectHistory, Object, SemanticNodeModel, IdentityEvidence, Identity)

EXPORT_FORMAT_VERSION = 1


def _iso(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


def list_facts(db: Any, include_superseded: bool = True) -> list[dict[str, Any]]:
    mem = ConversationalMemory(db)
    facts = mem.all_facts() if include_superseded else mem.active_facts()
    facts.sort(key=lambda f: f.timestamp or datetime.min)
    return [{"id": f.memory_id, "statement": f.statement, "status": f.status, "source": f.source,
             "recorded_at": _iso(f.timestamp), "key": f.key} for f in facts]


def list_objects(db: Any) -> list[dict[str, Any]]:
    return [{"name": name, "room": info.get("room"), "last_seen": info.get("last_seen")}
            for name, info in db.object_repo.get_all_objects().items() if info]


def list_people(db: Any) -> list[dict[str, Any]]:
    out = []
    for ident_id, info in db.get_all_identities().items():
        out.append({"id": ident_id, "name": info.get("display_name"), "relationship": info.get("relationship"),
                    "times_seen": info.get("times_seen"), "last_seen": info.get("last_seen"),
                    "face_embeddings": len(info.get("embeddings", []))})
    return out


def delete_fact(db: Any, memory_id: str) -> bool:
    """Permanently delete a stored fact; returns True only if it is verifiably gone."""
    existed = db.memory_repo.delete(memory_id)
    still_there = any(m.memory_id == memory_id for m in db.memory_repo.find_explicit())
    return existed and not still_there


def export_user_data(db: Any) -> dict[str, Any]:
    """Everything stored about the person, as plain JSON-serialisable data (no raw embeddings)."""
    with db.SessionFactory() as s:
        episodes = [{"id": e.id, "person": e.person, "summary": e.summary, "timestamp": e.timestamp,
                     "location": e.location, "tags": e.tags} for e in s.query(EpisodeModel).all()]
        history = [{"object": h.object_name, "timestamp": h.timestamp, "room": h.room}
                   for h in s.query(ObjectHistory).all()]
        preferred = s.query(SystemState).filter_by(key=PREFERRED_NAME_KEY).first()
    return {
        "format": "memora-user-export",
        "version": EXPORT_FORMAT_VERSION,
        "exported_at": datetime.now().isoformat(),
        "preferred_name": preferred.value if preferred else None,
        "facts": list_facts(db),
        "people": list_people(db),
        "objects": list_objects(db),
        "object_history": history,
        "episodes": episodes,
        "note": "Face embeddings are not exported; they are biometric data used only for recognition.",
    }


def write_export(db: Any, path: str) -> str:
    data = export_user_data(db)
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)  # personal data: owner read/write only
    except OSError:
        pass
    return path


def delete_all_user_data(db: Any) -> dict[str, Any]:
    """
    Remove all personal data (facts, episodes, people and their face embeddings,
    object sightings, preferred name) and verify that nothing remains.
    """
    for ident in list(db.identity_repo.get_all()):
        db.delete_identity(ident["identity_id"])
    with db._session_scope() as s:
        for model in PERSONAL_TABLES:
            s.query(model).delete()
        s.query(SystemState).filter(SystemState.key == PREFERRED_NAME_KEY).delete()

    with db.SessionFactory() as s:
        remaining = {m.__tablename__: s.query(m).count() for m in PERSONAL_TABLES}
    remaining["face_embeddings"] = len(db.vector_store)
    return {"ok": not any(remaining.values()), "remaining": remaining}
