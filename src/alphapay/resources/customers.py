from __future__ import annotations

from typing import Any, Dict, Optional

from ..http import Http


class CustomersResource:
    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``ordering``."""
        return self._http.request("GET", "/customers/", query=params)

    def create(
        self, *, country: str, phone: Optional[str] = None, full_name: Optional[str] = None, email: Optional[str] = None
    ) -> Dict[str, Any]:
        body = {k: v for k, v in dict(country=country, phone=phone, full_name=full_name, email=email).items() if v is not None}
        return self._http.request("POST", "/customers/", body=body)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/customers/{id}/")

    def update(self, id: str, **params: Any) -> Dict[str, Any]:
        return self._http.request("PATCH", f"/customers/{id}/", body=params)

    def delete(self, id: str) -> None:
        self._http.request("DELETE", f"/customers/{id}/")

    def transactions(self, id: str, **params: Any) -> Dict[str, Any]:
        """Contrairement à ``TransactionsResource.list()``, cet endpoint EST
        paginé par page (``page`` fonctionne ici) -- ``CustomerTransactionsView``
        n'a pas de ``pagination_class`` propre, il retombe donc sur le
        défaut global (``StandardResultsPagination``), pas
        ``CreatedAtCursorPagination``.
        """
        return self._http.request("GET", f"/customers/{id}/transactions/", query=params)
