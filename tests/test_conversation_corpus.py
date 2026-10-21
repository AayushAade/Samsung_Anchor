"""
Phrasing coverage, measured through the real pipeline against
tests/data/conversation_corpus.json. Add new phrasings there as they are found.
"""

from __future__ import annotations

from pathlib import Path

import json
import os

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from tests.consent_helpers import allow_memory

CORPUS = os.path.join(os.path.dirname(__file__), "data", "conversation_corpus.json")


def test_corpus_coverage():
    data = json.loads(Path(CORPUS).read_text())
    p = allow_memory(CognitivePipeline(MemoraDatabase(":memory:")))

    def say(u):
        return p.process(user_speech=u, return_dict=True)["speech_response"] or ""

    for line in data["setup"]:
        say(line)
    misses = [(c["say"], say(c["say"])) for c in data["cases"]]
    misses = [(s, r) for (s, r), c in zip(misses, data["cases"]) if c["expect"].lower() not in r.lower()]
    p.shutdown()
    assert misses == [], misses


def test_timeline_keeps_apostrophes():
    p = allow_memory(CognitivePipeline(MemoraDatabase(":memory:")))
    p.process(user_speech="I'm feeling a bit tired", return_dict=True)
    reply = p.process(user_speech="What did I do today?", return_dict=True)["speech_response"]
    assert "I'm feeling a bit tired" in reply
