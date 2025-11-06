"""Minimal HTTP API exposing the LangGraph agent."""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict

from agent.graph import graph


class AgentRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: HTTPStatus, payload: Dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # pragma: no cover - exercised manually
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # pragma: no cover - exercised manually
        if self.path != "/chat":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        user_input = str(payload.get("input", ""))
        if not user_input:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "missing input"})
            return
        result = graph.invoke({"input": user_input})
        self._send_json(HTTPStatus.OK, result)


def run(host: str = "0.0.0.0", port: int = 8080) -> None:  # pragma: no cover
    server = HTTPServer((host, port), AgentRequestHandler)
    print(f"Serving agent API on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover
    run()
