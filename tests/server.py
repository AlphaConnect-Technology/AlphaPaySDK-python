"""Petit serveur HTTP de test, lancé dans un thread du process de test
(pas un sous-processus -- Python évite ainsi les pièges de proc_open
rencontrés côté SDK PHP jumeau). Chaque route reproduit un scénario précis
de l'enveloppe StandardJSONRenderer côté AlphaPayBack.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional


class _Handler(BaseHTTPRequestHandler):
    server_version = "AlphaPayTestFixture/0.1"
    attempts: dict = {}

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - signature imposée par BaseHTTPRequestHandler
        pass  # silencieux -- pas de bruit dans la sortie des tests

    def _send_json(self, status: int, payload: dict, extra_headers: Optional[dict] = None) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - nom imposé par BaseHTTPRequestHandler
        if self.path == "/transactions/tx_1/":
            self._send_json(200, {"success": True, "data": {"id": "tx_1", "reference": "REF1"}, "code": 200})
            return
        if self.path == "/transactions/":
            self._send_json(
                200,
                {
                    "success": True,
                    "data": {"next": f"http://{self.headers['Host']}/transactions/page2/", "previous": None, "results": [{"id": "tx_1"}]},
                    "code": 200,
                },
            )
            return
        if self.path == "/transactions/page2/":
            self._send_json(
                200,
                {
                    "success": True,
                    "data": {"next": None, "previous": f"http://{self.headers['Host']}/transactions/", "results": [{"id": "tx_2"}]},
                    "code": 200,
                },
            )
            return
        if self.path == "/retry-then-success/":
            _Handler.attempts["retry_then_success"] = _Handler.attempts.get("retry_then_success", 0) + 1
            if _Handler.attempts["retry_then_success"] < 2:
                self._send_json(429, {"success": False, "error": {"detail": "Throttled"}, "code": 429}, {"Retry-After": "0"})
                return
            self._send_json(200, {"success": True, "data": {"id": "ok"}, "code": 200})
            return
        if self.path == "/always-429/":
            self._send_json(429, {"success": False, "error": {"detail": "Throttled"}, "code": 429}, {"Retry-After": "0"})
            return
        self._send_json(404, {"success": False, "error": {"detail": f"Not found: {self.path}"}, "code": 404})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)  # corps ignoré -- ces routes ne le lisent pas, sauf echo-headers ci-dessous

        if self.path == "/settlements/":
            self._send_json(400, {"success": False, "error": {"amount": ["Ce champ est requis."]}, "code": 400})
            return
        if self.path == "/echo-headers/":
            self._send_json(201, {"success": True, "data": {"idempotency_key": self.headers.get("Idempotency-Key")}, "code": 201})
            return
        if self.path == "/reset-counters/":
            _Handler.attempts.clear()
            self._send_json(200, {"success": True, "data": None, "code": 200})
            return
        self._send_json(404, {"success": False, "error": {"detail": f"Not found: {self.path}"}, "code": 404})


class TestServer:
    """Utilisable en context manager : ``with TestServer() as base_url: ...``"""

    def __init__(self) -> None:
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self._thread.start()
        port = self._httpd.server_address[1]
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *exc_info) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=2)

    def reset(self) -> None:
        _Handler.attempts.clear()
