"""The dashboard's WebSocket stream is only readable by the dashboard's own origin."""

from __future__ import annotations

import asyncio
import socket
import time

import pytest
from websockets.asyncio.client import connect

from experience.server import ExperienceServer


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    srv = ExperienceServer(port=port)
    srv.start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    return port


def _try(port, origin):
    async def go():
        async with connect(f"ws://127.0.0.1:{port}/ws", origin=origin, open_timeout=3):
            return True
    try:
        return asyncio.run(go())
    except Exception as e:
        return type(e).__name__


def test_foreign_website_cannot_read_stream(server):
    assert _try(server, "http://evil.example") != True


def test_dashboard_origin_can_connect(server):
    assert _try(server, f"http://localhost:{server}") is True


def test_static_files_cannot_escape_dashboard_dir(server):
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", server, timeout=3)
    conn.request("GET", "/../server.py")
    assert conn.getresponse().status in (403, 404)
