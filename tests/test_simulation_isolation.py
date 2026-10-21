"""
`app.py --simulate` must not touch the normal application environment: the
configured database location, the configured log directory, or anything else
outside its own temporary workspace (which it removes afterwards).
"""

from __future__ import annotations

from pathlib import Path

import hashlib
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _snapshot(root):
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            out[p] = (os.stat(p).st_mtime_ns, hashlib.sha256(Path(p).read_bytes()).hexdigest())
    return out


def test_simulate_leaves_normal_environment_untouched(tmp_path):
    normal = tmp_path / "normal"
    (normal / "logs").mkdir(parents=True)
    (normal / "logs" / "memora.log").write_text("existing log line\n")
    (normal / "memora_v2.sqlite").write_bytes(b"")  # placeholder for the person's database
    before = _snapshot(normal)
    tmp_before = set(os.listdir(tempfile.gettempdir()))

    env = dict(os.environ, MEMORA_DB_PATH=str(normal / "memora.sqlite"), MEMORA_LOG_DIR=str(normal / "logs"))
    r = subprocess.run([sys.executable, "app.py", "--simulate", "names_and_time", "restart_persistence"],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "2/2 journeys passed" in r.stdout

    assert _snapshot(normal) == before, "simulation modified the normal database or log directory"
    leftovers = {n for n in set(os.listdir(tempfile.gettempdir())) - tmp_before if n.startswith("memora-sim")}
    assert not leftovers, f"simulation left temporary workspaces behind: {leftovers}"
