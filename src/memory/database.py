"""
MemoraDatabase Architecture & Facade.

This module provides the central database facade for MEMORA (Samsung Anchor),
integrating SQLAlchemy ORM persistence with FAISS 128D vector similarity search.
It maintains full backward compatibility for all repository operations while providing
robust URL resolution, transaction safety, context manager support, and thread locks.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from src.memory.models import Base, Identity, IdentityEvidence, SystemState
from src.memory.repositories.episode_repository import DatabaseEpisodeRepository
from src.memory.repositories.identity_repository import IdentityRepository
from src.memory.repositories.memory_repository import DatabaseMemoryRepository
from src.memory.repositories.object_repository import ObjectRepository
from src.memory.vector_store import FaissVectorStore, VectorStoreError

logger = logging.getLogger(__name__)

# ============================================================================
# Constants & System Defaults
# ============================================================================
DEFAULT_CURRENT_ROOM: str = "Living Room"
KEY_NEXT_ANON_INDEX: str = "next_anon_index"
KEY_CURRENT_ROOM: str = "current_room"
STATUS_CONFIRMED: str = "confirmed"
MEMORY_DB_URL: str = "sqlite:///:memory:"
DB_MIGRATION_SUFFIX: str = "_v2.sqlite"


def resolve_db_url(db_path: str | None = None) -> tuple[str, str | None]:
    """
    Distinguishes between SQLAlchemy URLs and filesystem paths.

    Parameters
    ----------
    db_path : str | None
        Input database path, SQLAlchemy URL, or None (defaults to settings.DB_PATH).

    Returns
    -------
    tuple[str, str | None]
        A tuple of (sqlalchemy_url, filesystem_path_or_none).

    Examples
    --------
    - "memora_db.sqlite" -> ("sqlite:///memora_db_v2.sqlite", "memora_db_v2.sqlite")
    - "memora_db_v2.sqlite" -> ("sqlite:///memora_db_v2.sqlite", "memora_db_v2.sqlite")
    - "sqlite:///:memory:" -> ("sqlite:///:memory:", None)
    - ":memory:" -> ("sqlite:///:memory:", None)
    """
    raw_path = db_path or settings.DB_PATH

    # Check for in-memory indicators
    if raw_path == MEMORY_DB_URL or raw_path == ":memory:" or raw_path.startswith("sqlite:///:memory:"):
        return MEMORY_DB_URL, None

    # Check if raw_path is already a SQLAlchemy URL
    if "://" in raw_path:
        prefix = "sqlite:///"
        if raw_path.startswith(prefix):
            fs_target = _v2_filesystem_target(raw_path[len(prefix):])
            return f"{prefix}{fs_target}", fs_target
        return raw_path, None

    fs_target = _v2_filesystem_target(raw_path)
    return f"sqlite:///{fs_target}", fs_target


def _v2_filesystem_target(path: str) -> str:
    """
    Map a database path onto the schema-v2 file name.

    "memora_db.sqlite" historically maps to "memora_db_v2.sqlite". That mapping
    is applied only when the requested file does not already exist on its own;
    an existing database file passed explicitly is opened as-is rather than
    being silently replaced by a new, empty "_v2" sibling.
    """
    if path.endswith(DB_MIGRATION_SUFFIX):
        return path
    v2 = path.replace(".sqlite", DB_MIGRATION_SUFFIX) if ".sqlite" in path else f"{path}{DB_MIGRATION_SUFFIX}"
    if os.path.exists(path) and not os.path.exists(v2):
        return path
    return v2


class DatabaseUnavailableError(RuntimeError):
    """The configured memory database could not be opened; nothing was changed."""


def open_user_database(db_path: str | None = None) -> "MemoraDatabase":
    """
    Open the configured database, turning low-level failures (corrupt file,
    unwritable location, locked file) into one actionable error.
    """
    from sqlalchemy.exc import SQLAlchemyError

    target = db_path or settings.DB_PATH
    try:
        return MemoraDatabase(target)
    except (SQLAlchemyError, OSError) as e:
        resolved = resolve_db_url(target)[1] or target
        reason = str(getattr(e, "orig", None) or e).split("\n")[0]
        raise DatabaseUnavailableError(
            f"MEMORA could not open its memory file at {resolved} ({reason}). Nothing was changed.\n"
            "What you can do:\n"
            "  - If the file is damaged, restore a backup: python app.py --restore <backup folder>\n"
            "  - If the folder is not writable, fix its permissions or set MEMORA_DB_PATH to another location\n"
            "  - To start fresh, move the file somewhere safe first (do not delete it until you are sure)"
        ) from e


def restrict_permissions(path: str) -> None:
    """Personal data files are readable and writable by their owner only (0600)."""
    try:
        if os.path.exists(path):
            os.chmod(path, 0o600)
    except OSError as e:  # e.g. a file owned by another user on a shared volume
        logger.warning("Could not restrict permissions on %s: %s", path, e)


def vector_store_paths(db_path: str) -> tuple[str, str]:
    """Face-embedding files that belong to the database file at db_path."""
    base = os.path.splitext(os.path.abspath(db_path))[0]
    return f"{base}.faces.index", f"{base}.faces.json"


def _legacy_vector_store_paths(db_path: str) -> tuple[str, str] | None:
    """
    Older releases stored embeddings as face_embeddings.index / face_mapping.json
    next to the default database. They are adopted (read-only) only when the
    default database itself is opened.
    """
    default_fs = resolve_db_url(settings.DB_PATH)[1]
    if default_fs is None or os.path.abspath(db_path) != os.path.abspath(default_fs):
        return None
    directory = os.path.dirname(os.path.abspath(db_path))
    return os.path.join(directory, "face_embeddings.index"), os.path.join(directory, "face_mapping.json")


def _build_engine(url: str) -> Engine:
    """
    Helper function to build a production-hardened SQLAlchemy Engine.

    Parameters
    ----------
    url : str
        SQLAlchemy connection URL string.

    Returns
    -------
    Engine
        Configured SQLAlchemy Engine.
    """
    connect_args = {"check_same_thread": False, "timeout": 30.0}
    kwargs: dict[str, Any] = {
        "connect_args": connect_args,
        "future": True,
    }
    if url == MEMORY_DB_URL or ":memory:" in url:
        from sqlalchemy.pool import StaticPool
        kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_pre_ping"] = True

    return create_engine(url, **kwargs)


class MemoraDatabase:
    """
    Facade for the SQLAlchemy ORM + FAISS vector store architecture.

    Provides high-level persistent memory storage for identity embeddings,
    object spatial tracking, daily cognitive episodes, and system state while
    maintaining complete backward compatibility with the legacy SQLite API.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize MemoraDatabase.

        Parameters
        ----------
        db_path : str | None
            Filesystem database path, SQLAlchemy connection URL, or None.
        """
        self.db_url, self.db_path = resolve_db_url(db_path)

        if self.db_path is not None:
            abs_dir = os.path.dirname(os.path.abspath(self.db_path))
            if abs_dir:
                os.makedirs(abs_dir, exist_ok=True)

        self.engine = _build_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        if self.db_path is not None:
            restrict_permissions(self.db_path)

        self.SessionFactory = sessionmaker(bind=self.engine)
        self.lock = threading.Lock()

        # Initialize Sub-Repositories
        if self.db_path is not None:
            index_path, mapping_path = vector_store_paths(self.db_path)
            self.vector_store = FaissVectorStore(
                index_path, mapping_path, legacy_paths=_legacy_vector_store_paths(self.db_path)
            )
        else:
            # In-memory databases get an in-memory vector store: no filesystem access.
            self.vector_store = FaissVectorStore()
        self.identity_repo = IdentityRepository(self.SessionFactory)
        self.object_repo = ObjectRepository(self.SessionFactory)
        self.episode_repo = DatabaseEpisodeRepository(self.SessionFactory)
        self.memory_repo = DatabaseMemoryRepository(self.SessionFactory)

        self._init_system_state()
        logger.info("MemoraDatabase initialized successfully with URL: %s", self.db_url)

    @property
    def session_factory(self):
        return self.SessionFactory

    def __enter__(self) -> "MemoraDatabase":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """
        Dispose engine resources and clean up connection pool.
        Thread safety: Safe.
        """
        if hasattr(self, "engine") and self.engine is not None:
            self.engine.dispose()
            logger.info("MemoraDatabase engine disposed successfully.")

    @contextmanager
    def _session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.exception("Database transaction failed: %s", e)
            raise
        finally:
            session.close()

    def _init_system_state(self) -> None:
        with self._session_scope() as session:
            if not session.query(SystemState).filter_by(key=KEY_NEXT_ANON_INDEX).first():
                session.add(SystemState(key=KEY_NEXT_ANON_INDEX, value="1"))
            if not session.query(SystemState).filter_by(key=KEY_CURRENT_ROOM).first():
                session.add(SystemState(key=KEY_CURRENT_ROOM, value=DEFAULT_CURRENT_ROOM))

    def _get_system_state(self, key: str, default: str | None = None) -> str | None:
        with self.SessionFactory() as session:
            state = session.query(SystemState).filter_by(key=key).first()
            return state.value if state else default

    def _set_system_state(self, key: str, value: Any) -> None:
        with self._session_scope() as session:
            state = session.query(SystemState).filter_by(key=key).first()
            if state:
                state.value = str(value)
            else:
                session.add(SystemState(key=key, value=str(value)))

    @property
    def data(self) -> dict[str, Any]:
        """
        Legacy dictionary property representation of system state.

        Returns
        -------
        dict[str, Any]
        """
        return {
            "identities": self.get_all_identities(),
            "next_anon_index": int(self._get_system_state(KEY_NEXT_ANON_INDEX, "1") or 1),
            "objects": self.object_repo.get_all_objects(),
            "current_room": self._get_system_state(KEY_CURRENT_ROOM, DEFAULT_CURRENT_ROOM),
        }

    def load(self) -> None:
        """Legacy compatibility hook."""
        pass

    def save(self) -> None:
        """Legacy compatibility hook."""
        pass

    def find_match(
        self, query_embedding: Any, tolerance: float | None = None
    ) -> tuple[str | None, dict[str, Any] | None, float | None]:
        """
        Find closest matching face identity in FAISS vector store.

        Parameters
        ----------
        query_embedding : Any
            128D numpy feature vector.
        tolerance : float | None
            L2 match threshold distance.

        Returns
        -------
        tuple[str | None, dict[str, Any] | None, float | None]
            Tuple of (identity_id, identity_info_dict, distance).
        """
        if tolerance is None:
            tolerance = settings.FACE_TOLERANCE

        with self.lock:
            identity_id, faiss_id, distance = self.vector_store.find_match(query_embedding, tolerance)
            if identity_id is not None:
                identity_info = self.identity_repo.get_by_id(identity_id)
                if identity_info:
                    identity_info["embedding_row_id"] = faiss_id
                    identity_info["embeddings"] = self.vector_store.get_embeddings_for_identity(identity_id)
                return identity_id, identity_info, distance

        return None, None, None

    def register_anonymous(self, embedding: Any) -> str:
        """
        Register a new anonymous identity with embedding vector.

        Parameters
        ----------
        embedding : Any
            128D face feature vector.

        Returns
        -------
        str
            Generated anonymous identity string (e.g., 'Anonymous_ID_1').
        """
        with self.lock:
            anon_index = int(self._get_system_state(KEY_NEXT_ANON_INDEX, "1") or 1)
            anon_id = f"Anonymous_ID_{anon_index}"

            self._set_system_state(KEY_NEXT_ANON_INDEX, str(anon_index + 1))
            self.identity_repo.register_anonymous(anon_id)
            try:
                self.vector_store.add_embedding(anon_id, embedding)
            except VectorStoreError:
                # Never leave an identity row without the embedding that defines it.
                self._delete_identity_rows(anon_id)
                raise
            logger.info("Registered new anonymous identity: %s", anon_id)

            return anon_id

    def add_embedding_to_identity(self, identity_id: str, embedding: Any) -> bool:
        """
        Add a feature embedding vector to an existing identity.
        """
        with self.lock:
            identity = self.identity_repo.get_by_id(identity_id)
            if not identity:
                return False

            self.vector_store.add_embedding(identity_id, embedding)
            self.identity_repo.increment_times_seen(identity_id)
            return True

    def update_embedding_ema(
        self, embedding_id: int | None, new_embedding: Any, alpha: float = 0.1
    ) -> None:
        """
        Update stored FAISS vector embedding using Exponential Moving Average.
        """
        with self.lock:
            if embedding_id is not None:
                self.vector_store.update_embedding_ema(embedding_id, new_embedding, alpha)

    def increment_times_seen(self, identity_id: str) -> None:
        """
        Increment observation count for a given identity.
        """
        with self.lock:
            self.identity_repo.increment_times_seen(identity_id)

    def bind_name(self, identity_id: str, name: str, relationship: str | None = None) -> bool:
        """
        Bind a human display name and relationship to an identity record.
        """
        with self.lock:
            with self._session_scope() as session:
                identity = session.query(Identity).filter_by(identity_id=identity_id).first()
                if not identity:
                    return False
                identity.display_name = name
                identity.relationship = relationship
                identity.status = STATUS_CONFIRMED
                identity.confidence = 1.0
                logger.info("Bound name '%s' (relationship: %s) to identity %s", name, relationship, identity_id)
            return True

    def _delete_identity_rows(self, identity_id: str) -> bool:
        with self._session_scope() as session:
            session.query(IdentityEvidence).filter_by(identity_id=identity_id).delete()
            deleted = session.query(Identity).filter_by(identity_id=identity_id).delete()
        return bool(deleted)

    def delete_identity(self, identity_id: str) -> dict[str, Any]:
        """
        Permanently delete an identity, its name evidence, and its face embeddings.

        Returns a report of what was removed so callers can confirm deletion.
        """
        with self.lock:
            embeddings_removed = self.vector_store.remove_identity(identity_id)
            row_removed = self._delete_identity_rows(identity_id)
        return {"identity_id": identity_id, "record_deleted": row_removed,
                "embeddings_deleted": embeddings_removed}

    def check_integrity(self) -> dict[str, Any]:
        """
        Cross-check SQLite identities against the face-embedding store.

        Returns a dict with ``ok`` plus the specific inconsistencies found.
        """
        identity_ids = {i["identity_id"] for i in self.identity_repo.get_all()}
        embedded_ids = self.vector_store.identity_ids()
        report = {
            "identities": len(identity_ids),
            "embeddings": len(self.vector_store),
            "vector_store_persistent": self.vector_store.persistent,
            "vector_store_path": self.vector_store.mapping_path,
            "identities_without_embeddings": sorted(identity_ids - embedded_ids),
            "orphan_embedding_identities": sorted(embedded_ids - identity_ids),
            "vector_store_load_error": self.vector_store.load_error,
            "vector_store_save_error": self.vector_store.last_save_error,
        }
        report["ok"] = not (report["identities_without_embeddings"] or report["orphan_embedding_identities"]
                            or report["vector_store_load_error"] or report["vector_store_save_error"])
        return report

    def get_identity(self, identity_id: str) -> dict[str, Any] | None:
        """
        Fetch identity dictionary payload by identity ID.
        """
        identity_info = self.identity_repo.get_by_id(identity_id)
        if identity_info:
            identity_info["embeddings"] = self.vector_store.get_embeddings_for_identity(identity_id)
        return identity_info

    def get_all_identities(self) -> dict[str, dict[str, Any]]:
        """
        Fetch map of all identity records keyed by identity ID.
        """
        identities_list = self.identity_repo.get_all()
        result = {}
        for info in identities_list:
            info["embeddings"] = self.vector_store.get_embeddings_for_identity(info["identity_id"])
            result[info["identity_id"]] = info
        return result

    def log_object(
        self,
        object_name: str,
        x: float,
        y: float,
        room: str,
        bounding_box: Any = None,
    ) -> Any:
        """
        Log an observed physical object location to spatial memory.
        """
        with self.lock:
            return self.object_repo.log_object(object_name, x, y, room, bounding_box)

    def get_last_known_location(self, object_name: str) -> dict[str, Any] | None:
        """
        Fetch last known spatial location record for an object.
        """
        return self.object_repo.get_last_known_location(object_name)

    def get_object_history(self, object_name: str) -> list[Any]:
        """
        Fetch spatial observation history for an object.
        """
        loc = self.object_repo.get_last_known_location(object_name)
        return loc["history"] if loc else []

    def set_current_room(self, room_name: str) -> bool:
        """
        Update the system's active room location state.
        """
        self._set_system_state(KEY_CURRENT_ROOM, room_name)
        return True

    def get_current_room(self) -> str:
        """
        Fetch current active room location.
        """
        return self._get_system_state(KEY_CURRENT_ROOM, DEFAULT_CURRENT_ROOM) or DEFAULT_CURRENT_ROOM

    def clear(self) -> None:
        """
        Reset database schema and clear FAISS vector store.
        Thread safety: Safe.
        """
        with self.lock:
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)
            self.vector_store.clear()
            self._init_system_state()
            logger.info("Database schema reset and cleared successfully.")

    def add_evidence(
        self,
        identity_id: str,
        name: str,
        relationship: str | None = None,
        raw_transcript: str | None = None,
    ) -> Any:
        """
        Record identity speech evidence candidate.
        """
        with self.lock:
            return self.identity_repo.add_evidence(identity_id, name, relationship, raw_transcript)

    def get_candidates(self, identity_id: str) -> list[dict[str, Any]]:
        """
        Fetch recorded name candidates for an identity.
        """
        with self.SessionFactory() as session:
            evidences = (
                session.query(IdentityEvidence)
                .filter_by(identity_id=identity_id)
                .order_by(IdentityEvidence.confidence.desc())
                .all()
            )
            return [
                {
                    "name": ev.heard_name,
                    "relationship": ev.heard_relationship,
                    "count": ev.count,
                    "confidence": ev.confidence,
                }
                for ev in evidences
            ]
