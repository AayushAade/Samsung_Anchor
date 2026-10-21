"""
Create and verify a clean, separate MEMORA development database.

    python deployment/create_dev_database.py ~/memora-data/dev

Refuses to run if the target database already exists or is the project's default
database (memora_db_v2.sqlite in the project folder), so it can never migrate, overwrite
or re-permission existing data. On success it prints the variables to export.
"""

from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PERSONAL_TABLES = ("relevant_memories", "episodes", "objects", "object_history", "identities",
                   "identity_evidence", "semantic_nodes", "care_items", "care_events",
                   "interaction_records", "feedback_events")


def create(directory: str) -> dict:
    directory = os.path.abspath(os.path.expanduser(directory))
    requested = os.path.join(directory, "memora.sqlite")
    actual = os.path.join(directory, "memora_v2.sqlite")
    default_db = os.path.join(ROOT, "memora_db_v2.sqlite")
    if os.path.abspath(actual) == os.path.abspath(default_db) or directory == ROOT:
        raise SystemExit("Refusing: that is the project's default database location.")
    for path in (requested, actual):
        if os.path.exists(path):
            raise SystemExit(f"Refusing: {path} already exists. Choose an empty folder.")

    os.makedirs(os.path.join(directory, "logs"), mode=0o700, exist_ok=True)
    from src.memory.database import MemoraDatabase
    with MemoraDatabase(requested) as db:
        created = db.db_path
    if os.path.abspath(created) != actual:
        raise SystemExit(f"Unexpected database location: {created}")

    con = sqlite3.connect(f"file:{created}?mode=ro", uri=True)
    try:
        counts = {t: con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in PERSONAL_TABLES}
        version = con.execute("select value from system_state where key='schema_version'").fetchone()
    finally:
        con.close()
    mode = oct(os.stat(created).st_mode & 0o777)
    report = {"database": created, "schema_version": version[0] if version else None,
              "personal_rows": sum(counts.values()), "mode": mode}
    if report["personal_rows"] != 0 or mode != "0o600" or report["schema_version"] is None:
        raise SystemExit(f"Verification failed: {report}")
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    report = create(argv[1])
    directory = os.path.dirname(report["database"])
    print(f"Created and verified {report['database']}: schema version {report['schema_version']}, "
          f"{report['personal_rows']} personal rows, mode {report['mode'][2:]}.")
    print("Use it with:")
    print(f"  export MEMORA_DB_PATH={os.path.join(directory, 'memora.sqlite')}")
    print(f"  export MEMORA_LOG_DIR={os.path.join(directory, 'logs')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
