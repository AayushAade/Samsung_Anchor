"""
Versioned, additive schema migrations for the MEMORA SQLite database.

`Base.metadata.create_all` creates missing tables but never alters existing
ones, so columns added to existing tables need an explicit migration.

Rules:
- Migrations are additive (new nullable columns / tables) so older data stays
  valid and an older MEMORA build can still read the file.
- Each migration runs once; the applied version is stored in system_state
  under "schema_version".
- Migrations run inside a transaction; on failure nothing is changed and the
  error propagates (the caller reports it and leaves the file untouched).
- Rollback: restore the automatic pre-migration backup or a --backup copy.
"""

from __future__ import annotations

import logging
from typing import Callable

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

logger = logging.getLogger(__name__)

SCHEMA_VERSION_KEY = "schema_version"


def _add_column_if_missing(conn: Connection, table: str, column: str, ddl_type: str) -> None:
    cols = {c["name"] for c in inspect(conn).get_columns(table)}
    if column not in cols:
        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {ddl_type}'))


def _m1_object_source(conn: Connection) -> None:
    """Object sightings record where they came from (REAL_CAMERA, SIMULATED_CAMERA, ...)."""
    _add_column_if_missing(conn, "objects", "source", "VARCHAR")
    _add_column_if_missing(conn, "object_history", "source", "VARCHAR")


MIGRATIONS: list[tuple[int, str, Callable[[Connection], None]]] = [
    (1, "object sighting source", _m1_object_source),
]
LATEST_VERSION = MIGRATIONS[-1][0]


def current_version(conn: Connection) -> int:
    row = conn.execute(text("SELECT value FROM system_state WHERE key = :k"), {"k": SCHEMA_VERSION_KEY}).first()
    try:
        return int(row[0]) if row else 0
    except (TypeError, ValueError):
        return 0


def migrate(engine) -> list[str]:
    """Apply pending migrations. Returns the descriptions of migrations applied."""
    applied = []
    with engine.begin() as conn:
        version = current_version(conn)
        if version > LATEST_VERSION:
            raise RuntimeError(f"Database schema version {version} is newer than this MEMORA build "
                               f"supports ({LATEST_VERSION}). Use a newer MEMORA version.")
        for number, description, fn in MIGRATIONS:
            if number > version:
                fn(conn)
                applied.append(description)
                version = number
        conn.execute(text("INSERT INTO system_state (key, value) VALUES (:k, :v) "
                          "ON CONFLICT(key) DO UPDATE SET value = excluded.value"),
                     {"k": SCHEMA_VERSION_KEY, "v": str(version)})
    if applied:
        logger.info("Applied schema migrations: %s", ", ".join(applied))
    return applied
