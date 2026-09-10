"""
Client HTTP bas niveau, partagé par toutes les ressources. Gère
l'authentification, l'enveloppe standard {success, data, code}, les retries
avec backoff sur 429/5xx/erreur réseau, et le mapping vers des exceptions
typées (cf. exceptions.py) -- chaque ressource (Transactions, PaymentLinks,
...) n'a plus qu'à décrire le endpoint, jamais la mécanique réseau.

Volontairement stdlib uniquement (urllib), pas de dépendance à `requests` --
cohérent avec les SDK Node/PHP jumeaux (0 dépendance runtime).
"""

from __future__ import annotations

import json
import random
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from .exceptions import (
    AlphaPayConnectionError,
    AlphaPayError,
    AlphaPayRateLimitError,
    AlphaPayServerError,
    error_from_response,
)

DEFAULT_BASE_URL = "https://api.alphapay.me/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class Http:
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise ValueError("AlphaPayClient: `api_key` est requis.")
        self._api_key = api_key
        self.environment = "live" if api_key.startswith("sk_live_") else "sandbox"
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        idempotency_key: Union[str, bool, None] = None,
    ) -> Any:
        # `path` est une URL absolue quand on suit un lien "next"/"previous"
        # renvoyé tel quel par l'API (cf. pagination.paginate()) -- déjà
        # complète, avec sa propre query string ; ne jamais la préfixer par
        # base_url ni y rajouter `query` par-dessus.
        if path.startswith("http://") or path.startswith("https://"):
            url = path
        else:
            qs = self._build_query_string(query)
            url = f"{self.base_url}{path}{qs}"

        headers = {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}
        data: Optional[bytes] = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        if idempotency_key:
            key = idempotency_key if isinstance(idempotency_key, str) else self._random_idempotency_key()
            headers["Idempotency-Key"] = key

        attempt = 0
        while True:
            try:
                return self._attempt(method, url, headers, data)
            except (AlphaPayRateLimitError, AlphaPayServerError) as exc:
                if attempt >= self._max_retries:
                    raise
                retry_after = getattr(exc, "retry_after", None)
                delay = retry_after if retry_after is not None else self._backoff_seconds(attempt)
                time.sleep(delay)
                attempt += 1
            except AlphaPayConnectionError:
                if attempt >= self._max_retries:
                    raise
                time.sleep(self._backoff_seconds(attempt))
                attempt += 1

    def request_binary(self, path: str) -> Dict[str, Any]:
        """Pour les rares endpoints qui répondent en binaire plutôt qu'en JSON
        (ex. GET /transactions/{id}/invoice/, application/pdf, et
        /transactions/export/, text/csv) -- bypass l'enveloppe standard,
        jamais utilisée par un endpoint qui en renvoie une.

        Retourne {"data": bytes, "content_type": str|None, "filename": str|None}.
        """
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self._api_key}", "Accept": "application/pdf, text/csv, application/octet-stream"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type")
                filename = self._extract_filename(response.headers.get("Content-Disposition"))
                return {"data": raw, "content_type": content_type, "filename": filename}
        except urllib.error.HTTPError as exc:
            # Une erreur sur cet endpoint reste en JSON (cf. InvoiceError côté API) --
            # on retombe sur le mapping JSON normal pour un message exploitable.
            raise self._error_from_http_error(exc) from exc
        except socket.timeout as exc:
            raise AlphaPayConnectionError("Requête AlphaPay expirée.", status=0) from exc
        except urllib.error.URLError as exc:
            raise AlphaPayConnectionError(f"Impossible de joindre l'API AlphaPay : {exc.reason}", status=0) from exc

    def _attempt(self, method: str, url: str, headers: Dict[str, str], data: Optional[bytes]) -> Any:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                body = response.read()
                request_id = response.headers.get("X-Request-Id")
                return self._unwrap_success(body, request_id)
        except urllib.error.HTTPError as exc:
            raise self._error_from_http_error(exc) from exc
        except socket.timeout as exc:
            raise AlphaPayConnectionError("Requête AlphaPay expirée.", status=0) from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            is_timeout = "timed out" in str(reason).lower()
            message = "Requête AlphaPay expirée." if is_timeout else f"Impossible de joindre l'API AlphaPay : {reason}"
            raise AlphaPayConnectionError(message, status=0) from exc

    def _error_from_http_error(self, exc: urllib.error.HTTPError) -> AlphaPayError:
        request_id = exc.headers.get("X-Request-Id") if exc.headers else None
        raw_body = exc.read()
        json_body = self._try_parse_json(raw_body)
        error_body = json_body.get("error") if isinstance(json_body, dict) and "error" in json_body else json_body
        error = error_from_response(exc.code, error_body, request_id)
        if isinstance(error, AlphaPayRateLimitError):
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            error.retry_after = int(retry_after) if retry_after else None
        return error

    def _unwrap_success(self, raw_body: bytes, request_id: Optional[str]) -> Any:
        json_body = self._try_parse_json(raw_body)
        if isinstance(json_body, dict) and "data" in json_body:
            return json_body["data"]
        return json_body

    @staticmethod
    def _try_parse_json(raw_body: bytes) -> Any:
        if not raw_body:
            return None
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            # Réponse non-JSON (page d'erreur d'un proxy en amont, ex. 502 Traefik) --
            # traité comme une absence de corps exploitable.
            return None

    @staticmethod
    def _build_query_string(query: Optional[Dict[str, Any]]) -> str:
        if not query:
            return ""
        filtered = {k: v for k, v in query.items() if v is not None}
        if not filtered:
            return ""
        return "?" + urllib.parse.urlencode(filtered)

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        # Backoff exponentiel + gigue : 0.4-0.6s, 0.8-1.2s, 1.6-2.4s...
        base = 0.4 * (2**attempt)
        return base + random.uniform(0, base * 0.5)

    @staticmethod
    def _random_idempotency_key() -> str:
        return f"idem_{secrets.token_hex(16)}"

    @staticmethod
    def _extract_filename(content_disposition: Optional[str]) -> Optional[str]:
        if not content_disposition:
            return None
        import re

        match = re.search(r'filename="?([^";]+)"?', content_disposition)
        return match.group(1) if match else None
