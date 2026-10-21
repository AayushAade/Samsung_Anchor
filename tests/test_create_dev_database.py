"""The clean development database tool must create a verified empty database and refuse
to touch an existing one or the project's default database."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "deployment", "create_dev_database.py")


def _run(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("MEMORA_")}
    return subprocess.run([sys.executable, TOOL, *args], cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=120)


def test_creates_a_verified_empty_database(tmp_path):
    proc = _run(str(tmp_path / "dev"))
    assert proc.returncode == 0, proc.stderr + proc.stdout
    db = tmp_path / "dev" / "memora_v2.sqlite"
    assert db.exists() and oct(os.stat(db).st_mode & 0o777) == "0o600"
    assert "0 personal rows" in proc.stdout and f"MEMORA_DB_PATH={tmp_path / 'dev' / 'memora.sqlite'}" in proc.stdout


def test_refuses_existing_database_without_changing_it(tmp_path):
    target = tmp_path / "dev"
    target.mkdir()
    existing = target / "memora_v2.sqlite"
    existing.write_bytes(b"owner data")
    before = hashlib.sha256(existing.read_bytes()).hexdigest()
    proc = _run(str(target))
    assert proc.returncode != 0 and "already exists" in proc.stderr + proc.stdout
    assert hashlib.sha256(existing.read_bytes()).hexdigest() == before


def test_refuses_the_project_default_location():
    default = os.path.join(ROOT, "memora_db_v2.sqlite")
    before = os.stat(default).st_mtime_ns if os.path.exists(default) else None
    proc = _run(ROOT)
    assert proc.returncode != 0 and "Refusing" in proc.stderr + proc.stdout
    assert (os.stat(default).st_mtime_ns if os.path.exists(default) else None) == before
