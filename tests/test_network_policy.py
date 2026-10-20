"""
Network policy (docs/PRIVACY_AND_CONSENT.md): text chat, simulation and the
default runtime make no outbound connections. Model downloads and cloud
services need explicit opt-in environment variables. Connections are
intercepted at the socket layer, so any library (httpx, requests, urllib,
SDKs) is covered.
"""

from __future__ import annotations

import socket

import pytest

from src.application.chat import ChatSession
from src.application.factory import build_application
from src.memory.database import MemoraDatabase


class _Blocked(OSError):
    pass


@pytest.fixture
def outbound(monkeypatch):
    attempts = []
    real_connect, real_connect_ex = socket.socket.connect, socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def _local(host):
        return str(host) in ("127.0.0.1", "::1", "localhost") or str(host).startswith("127.")

    def guarded_getaddrinfo(host, *a, **k):
        if host is not None and not _local(host):
            attempts.append(("dns", host))
            raise _Blocked(f"outbound DNS lookup blocked: {host}")
        return real_getaddrinfo(host, *a, **k)

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(address, tuple) and not _local(host):
            attempts.append(("connect", host))
            raise _Blocked(f"outbound connection blocked: {host}")
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(address, tuple) and not _local(host):
            attempts.append(("connect", host))
            return 111
        return real_connect_ex(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    for var in ("MEMORA_ALLOW_MODEL_DOWNLOAD", "MEMORA_ALLOW_CLOUD_ASR", "MEMORA_ALLOW_CLOUD_LLM"):
        monkeypatch.delenv(var, raising=False)
    return attempts


def test_chat_makes_no_outbound_connections(outbound, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")  # a key alone must not cause network use
    coord = build_application(live_hardware=False, database=MemoraDatabase(str(tmp_path / "n.sqlite")))
    s = ChatSession(coord, log_path=str(tmp_path / "log"))
    s.opening()
    for line in ("yes", "My name is Ana", "I like tea", "What do I like?", "Where are my keys?",
                 "Help me, I fell", "What time is it?"):
        s.handle(line)
    s.close()
    assert outbound == [], outbound


def test_simulation_journey_makes_no_outbound_connections(outbound):
    from src.simulation.journeys import all_journeys, run_journey
    journey = next(j for j in all_journeys() if j.name == "restart_persistence")
    assert run_journey(journey).passed
    assert outbound == [], outbound


def test_speech_model_is_not_loaded_or_downloaded_at_startup(outbound):
    from src.perception.speech_recognition_engine import SpeechRecognitionEngine
    engine = SpeechRecognitionEngine()
    assert engine.model is None  # lazily loaded only when voice transcription is requested
    assert outbound == []


def test_cloud_llm_needs_explicit_opt_in(monkeypatch):
    from src.reasoning.context_binder import MemoraContextBinder, cloud_llm_allowed
    monkeypatch.delenv("MEMORA_ALLOW_CLOUD_LLM", raising=False)
    assert cloud_llm_allowed() is False
    assert MemoraContextBinder(api_key="test-key-not-real").use_api is False
