"""
The real text product, end to end, through the command line a person uses:
first run and consent -> conversation -> spoken correction -> restart ->
backup -> damaged database -> diagnostics -> restore -> delete everything ->
restart. Synthetic data only; every file lives in a temporary workspace.
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(env, *args, stdin=""):
    proc = subprocess.run([sys.executable, "app.py", *args], cwd=ROOT, env=env, input=stdin,
                          capture_output=True, text=True, timeout=180)
    return proc.returncode, proc.stdout


def _chat(env, *lines):
    code, out = _run(env, "--chat", stdin="\n".join(lines) + "\n")
    assert code == 0, out
    return out


def test_text_product_journey(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("MEMORA_")}
    env.update(MEMORA_DB_PATH=str(tmp_path / "data" / "memora.sqlite"), MEMORA_LOG_DIR=str(tmp_path / "logs"),
               PYTHONDONTWRITEBYTECODE="1")
    (tmp_path / "data").mkdir()
    db_file = tmp_path / "data" / "memora_v2.sqlite"

    out = _chat(env, "yes", "My name is Asha", "My daughter is Riya",
                "Actually my daughter's name is Priya", "Who is my daughter?", "/quit")
    assert "Nice to meet you, Asha" in out and "I've updated that" in out
    assert "You told me today that your daughter's name is Priya." in out

    out = _chat(env, "Who is my daughter?", "What is my name?", "/quit")
    assert "Welcome back, Asha" in out and "daughter's name is Priya." in out and "is Riya." not in out

    code, out = _run(env, "--backup", str(tmp_path / "backups"))
    assert code == 0 and "verified" in out
    backup = next((tmp_path / "backups").glob("memora_backup_*"))

    data = bytearray(db_file.read_bytes())
    data[:4096] = b"\0" * 4096
    db_file.write_bytes(bytes(data))
    code, out = _run(env, "--check")
    assert code == 1 and f"Cannot open {db_file}" in out
    code, out = _run(env, "--chat", stdin="Who is my daughter?\n/quit\n")
    assert code == 2 and "--restore" in out and "Nothing was changed" in out

    code, out = _run(env, "--restore", str(backup), stdin="RESTORE\n")
    assert code == 0 and "Restored" in out

    out = _chat(env, "Who is my daughter?", "/delete-all", "DELETE", "/quit")
    assert "Priya" in out and "All your data has been deleted" in out

    out = _chat(env, "no", "Who is my daughter?", "/memories", "/quit")
    assert "Before we start" in out and "Asha" not in out and "Priya" not in out
    assert "You haven't told me anything to remember yet" in out
    for log in (tmp_path / "logs").glob("*"):
        assert b"Priya" not in log.read_bytes() and b"Asha" not in log.read_bytes()
