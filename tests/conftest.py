"""
Shared pytest configuration.

Every test session runs against a throwaway database directory so that the
suite can never read, modify, or delete the operator's real MEMORA data
(memora_db_v2.sqlite and its face-embedding files in the repository root).
"""

from __future__ import annotations

import os
import tempfile

import pytest

_SESSION_DIR = tempfile.mkdtemp(prefix="memora-tests-")
os.environ["MEMORA_DB_PATH"] = os.path.join(_SESSION_DIR, "memora_test_db.sqlite")
os.environ["MEMORA_LOG_DIR"] = os.path.join(_SESSION_DIR, "logs")

from config import settings  # noqa: E402  (must follow the environment override)

settings.DB_PATH = os.environ["MEMORA_DB_PATH"]
settings.LOG_DIR = os.environ["MEMORA_LOG_DIR"]


@pytest.fixture(autouse=True, scope="session")
def _isolated_database_path():
    real_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memora_db_v2.sqlite"))
    assert os.path.abspath(settings.DB_PATH) != real_default
    yield settings.DB_PATH
