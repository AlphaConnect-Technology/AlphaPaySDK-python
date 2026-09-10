from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..http import Http


class PaymentLinksResource:
    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``ordering``, ``is_active``."""
        return self._http.request("GET", "/payment-links/", query=params)

    def create(
        self,
        *,
        name: str,
        currency: str,
        description: Optional[str] = None,
        amount_type: Optional[str] = None,
        amount: Union[int, float, str, None] = None,
        min_amount: Union[int, float, str, None] = None,
        expires_at: Optional[str] = None,
        usage_limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        body = {
            k: v
            for k, v in dict(
                name=name,
                currency=currency,
                description=description,
                amount_type=amount_type,
                amount=amount,
                min_amount=min_amount,
                expires_at=expires_at,
                usage_limit=usage_limit,
            ).items()
            if v is not None
        }
        return self._http.request("POST", "/payment-links/", body=body)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/payment-links/{id}/")

    def update(self, id: str, **params: Any) -> Dict[str, Any]:
        return self._http.request("PATCH", f"/payment-links/{id}/", body=params)

    def delete(self, id: str) -> None:
        self._http.request("DELETE", f"/payment-links/{id}/")
