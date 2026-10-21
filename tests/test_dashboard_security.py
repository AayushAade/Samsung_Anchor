"""The dashboard's WebSocket stream is only readable by the dashboard's own origin."""

from __future__ import annotations

from pathlib import Path

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


def test_dashboard_loads_nothing_from_the_internet():
    """Found in review: the page fetched Google Fonts, an undisclosed third-party request."""
    import os
    import re
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experience", "dashboard")
    for name in os.listdir(root):
        text = Path(root, name).read_text(encoding="utf-8")
        external = [u for u in re.findall(r"(?:https?|wss?)://[^\s'\"`)<>]+", text)
                    if not re.match(r"(?:https?|wss?)://(?:localhost|127\.0\.0\.1|www\.w3\.org)\b", u)
                    and "${" not in u]
        assert external == [], f"{name}: {external}"
