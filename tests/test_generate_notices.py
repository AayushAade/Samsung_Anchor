"""Notices and SBOM come from installed package metadata, include bundled third-party
licence texts (e.g. OpenCV's FFmpeg/Qt notices) and never use the network."""

from __future__ import annotations

import importlib.util
import json
import socket
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("generate_notices", "deployment/generate_notices.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_notices_and_sbom_cover_installed_core_packages(tmp_path, monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("network used"))
    notices, sbom = gen.write(str(tmp_path))
    text = Path(notices).read_text(encoding="utf-8")
    for package in ("numpy", "SQLAlchemy", "faiss-cpu", "websockets"):
        assert f"\n{package} " in text
    assert "LICENSE-3RD-PARTY" in text          # OpenCV's notices for bundled libraries
    bom = json.loads(Path(sbom).read_text())
    assert bom["bomFormat"] == "CycloneDX" and bom["specVersion"] == "1.5"
    names = {c["name"].lower() for c in bom["components"]}
    assert {"numpy", "sqlalchemy", "faiss-cpu"} <= names
    assert all(c["purl"].startswith("pkg:pypi/") and c["licenses"] for c in bom["components"])
