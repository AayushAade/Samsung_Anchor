"""
Backup and restore of a MEMORA database and its face-embedding files.

- Backups use SQLite's online backup API, so they are consistent even while
  MEMORA is running.
- Each backup directory holds a manifest with SHA-256 checksums and row counts.
- Restore verifies checksums and opens the backup to run the integrity check
  *before* touching the live files, and saves the current files first.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from typing import Any, Optional

from src.memory.database import MemoraDatabase, restrict_permissions, vector_store_paths

MANIFEST = "manifest.json"
BACKUP_FORMAT = 1


class BackupError(RuntimeError):
    pass


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _row_counts(db_file: str) -> dict[str, int]:
    con = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        return {t: con.execute(f'select count(*) from "{t}"').fetchone()[0] for t in tables}
    finally:
        con.close()


def create_backup(db_path: str, dest_root: str) -> str:
    """Write a verified backup of db_path into a new directory under dest_root. Returns that directory."""
    if not os.path.exists(db_path):
        raise BackupError(f"Database not found: {db_path}")
    target = os.path.join(dest_root, f"memora_backup_{datetime.now():%Y%m%d_%H%M%S_%f}")
    os.makedirs(target, mode=0o700)
    db_name = os.path.basename(db_path)
    dst_db = os.path.join(target, db_name)

    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(dst_db)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    restrict_permissions(dst_db)

    files = {db_name: _sha256(dst_db)}
    for path in vector_store_paths(db_path):
        if os.path.exists(path):
            copy = os.path.join(target, os.path.basename(path))
            shutil.copy2(path, copy)
            restrict_permissions(copy)
            files[os.path.basename(path)] = _sha256(copy)

    manifest = {"format": BACKUP_FORMAT, "created_at": datetime.now().isoformat(),
                "source_db": os.path.abspath(db_path), "database_file": db_name,
                "files": files, "row_counts": _row_counts(dst_db)}
    with open(os.path.join(target, MANIFEST), "w") as f:
        json.dump(manifest, f, indent=2)
    restrict_permissions(os.path.join(target, MANIFEST))
    return target


def _check_names(manifest: dict[str, Any]) -> None:
    """A manifest may only name plain files inside the backup directory."""
    names = list(manifest.get("files", {})) + [manifest.get("database_file", "")]
    for name in names:
        if (not isinstance(name, str) or not name or name in (".", "..", MANIFEST)
                or os.path.basename(name) != name or "\\" in name):
            raise BackupError(f"Backup manifest names an invalid file: {name!r}")
    if manifest["database_file"] not in manifest["files"]:
        raise BackupError("Backup manifest does not list its database file")


def verify_backup(backup_dir: str) -> dict[str, Any]:
    """Check checksums and run the identity/embedding integrity check on a scratch copy."""
    with open(os.path.join(backup_dir, MANIFEST)) as f:
        manifest = json.load(f)
    _check_names(manifest)
    for name, digest in manifest["files"].items():
        path = os.path.join(backup_dir, name)
        if not os.path.exists(path) or _sha256(path) != digest:
            raise BackupError(f"Backup file missing or altered: {name}")
    scratch = tempfile.mkdtemp(prefix="memora-verify-")
    try:
        for name in manifest["files"]:
            shutil.copy2(os.path.join(backup_dir, name), os.path.join(scratch, name))
        db = MemoraDatabase(os.path.join(scratch, manifest["database_file"]))
        report = db.check_integrity()
        db.close()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return {"manifest": manifest, "integrity": report}


def restore_backup(backup_dir: str, db_path: str) -> dict[str, Any]:
    """
    Replace db_path (and its face files) with the backup, after verification.
    The current files are first saved to a 'pre-restore' backup next to the backup.
    """
    checked = verify_backup(backup_dir)
    manifest = checked["manifest"]
    pre_restore: Optional[str] = None
    if os.path.exists(db_path):
        # Raw byte copies of whatever is there now, even if it is corrupt (restore is
        # usually needed exactly when the live file can no longer be opened).
        pre_restore = os.path.join(os.path.dirname(os.path.abspath(backup_dir)),
                                   f"memora_pre-restore_{datetime.now():%Y%m%d_%H%M%S_%f}")
        os.makedirs(pre_restore, mode=0o700)
        for path in (db_path, *vector_store_paths(db_path)):
            if os.path.exists(path):
                copy = os.path.join(pre_restore, os.path.basename(path))
                shutil.copy2(path, copy)
                restrict_permissions(copy)

    live_files = {manifest["database_file"]: db_path}
    idx, mapping = vector_store_paths(db_path)
    live_files.update({os.path.basename(p): p for p in (idx, mapping)})
    # Remove live face files that the backup does not contain, so they cannot mismatch.
    for name, live in live_files.items():
        if name not in manifest["files"] and os.path.exists(live) and live != db_path:
            os.remove(live)
    for name in manifest["files"]:
        live = live_files.get(name)
        if live is None:  # face files from a differently named DB: map by suffix
            live = idx if name.endswith(".faces.index") else mapping if name.endswith(".faces.json") else db_path
        tmp = live + ".restore-tmp"
        shutil.copy2(os.path.join(backup_dir, name), tmp)
        os.replace(tmp, live)
        restrict_permissions(live)
    return {"restored_from": backup_dir, "pre_restore_backup": pre_restore,
            "integrity": checked["integrity"]}
