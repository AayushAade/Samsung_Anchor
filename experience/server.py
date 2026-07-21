"""
Memora Experience Server.

Lightweight WebSocket + HTTP server that bridges the CognitiveStream
to the browser-based Experience Dashboard.

Uses the `websockets` library (already installed) and Python's built-in
http.server for static file serving.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import webbrowser
from pathlib import Path
from typing import Set

import websockets
from websockets.asyncio.server import serve

from src.core.cognitive_stream import CognitiveStream, CognitiveEvent

# Path to the dashboard static files
DASHBOARD_DIR = Path(__file__).parent / "dashboard"


class ExperienceServer:
    """
    Serves the Experience Dashboard and streams cognitive events via WebSocket.
    """

    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._stream = CognitiveStream.instance()

    def start(self) -> None:
        """Start the server in a background thread."""
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

        # Subscribe to the cognitive stream
        self._stream.subscribe(self._on_cognitive_event)

    def _run_server(self) -> None:
        """Run the asyncio event loop in a background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self) -> None:
        """Start both the WebSocket and HTTP server."""
        # Start WebSocket server
        async with serve(
            self._ws_handler,
            self.host,
            self.port,
            process_request=self._http_handler,
        ):
            print(f"\n{'='*60}")
            print(f"  🧠 Memora Experience Platform")
            print(f"  Dashboard: http://{self.host}:{self.port}")
            print(f"  WebSocket: ws://{self.host}:{self.port}/ws")
            print(f"{'='*60}\n")
            await asyncio.Future()  # Run forever

    async def _http_handler(self, connection, request):
        """Serve static files for non-WebSocket requests."""
        from websockets.http11 import Response

        path = request.path

        # WebSocket upgrade — let it pass through
        if path == "/ws":
            return None

        # Map paths to files
        if path == "/" or path == "":
            file_path = DASHBOARD_DIR / "index.html"
        else:
            # Strip leading slash and serve from dashboard dir
            clean_path = path.lstrip("/")
            file_path = DASHBOARD_DIR / clean_path

        # Security: prevent path traversal
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(DASHBOARD_DIR.resolve())):
                return Response(403, "Forbidden", websockets.Headers())
        except Exception:
            return Response(404, "Not Found", websockets.Headers())

        if not file_path.exists() or not file_path.is_file():
            return Response(404, "Not Found", websockets.Headers())

        # Determine content type
        content_type = self._get_content_type(file_path)

        body = file_path.read_bytes()
        headers = websockets.Headers()
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(body))
        headers["Cache-Control"] = "no-cache"
        return Response(200, "OK", headers, body)

    async def _ws_handler(self, websocket):
        """Handle a new WebSocket connection."""
        self._clients.add(websocket)
        print(f"[ExperienceServer] Dashboard connected ({len(self._clients)} clients)")

        try:
            # Send history on connect (catch-up)
            history = self._stream.get_history()
            for event in history[-50:]:
                await websocket.send(event.to_json())

            # Keep connection alive
            async for message in websocket:
                # We don't expect messages from the client, but handle gracefully
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            print(f"[ExperienceServer] Dashboard disconnected ({len(self._clients)} clients)")

    def _on_cognitive_event(self, event: CognitiveEvent) -> None:
        """Callback from CognitiveStream — forward to all WebSocket clients."""
        if self._loop is None or not self._clients:
            return

        json_data = event.to_json()

        # Schedule the broadcast on the asyncio loop
        asyncio.run_coroutine_threadsafe(
            self._broadcast(json_data),
            self._loop,
        )

    async def _broadcast(self, data: str) -> None:
        """Send data to all connected WebSocket clients."""
        if not self._clients:
            return

        disconnected = set()
        for client in self._clients:
            try:
                await client.send(data)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)

        self._clients -= disconnected

    def open_dashboard(self) -> None:
        """Open the dashboard in the default browser."""
        import time
        time.sleep(0.5)  # Give server a moment to start
        webbrowser.open(f"http://{self.host}:{self.port}")

    @staticmethod
    def _get_content_type(path: Path) -> str:
        ext = path.suffix.lower()
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
            ".woff": "font/woff",
        }
        return content_types.get(ext, "application/octet-stream")
