from __future__ import annotations

from typing import Any, Dict, Union

from ..http import Http


class WalletTransfersResource:
    """Transferts entre les wallets multi-pays d'un même marchand (avec
    conversion automatique si les devises diffèrent).

    ATTENTION : entièrement inaccessible via clé API -- même restriction que
    :class:`SettlementsResource`, vérifiée en conditions réelles (403,
    ``error_code == "dashboard_only"``) : uniquement pilotable depuis le
    dashboard (compte utilisateur), jamais une clé API.
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``status``."""
        return self._http.request("GET", "/wallet-transfers/", query=params)

    def create(
        self,
        *,
        from_country: str,
        to_country: str,
        from_amount: Union[int, float, str],
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        body = {"from_country": from_country, "to_country": to_country, "from_amount": from_amount}
        return self._http.request("POST", "/wallet-transfers/", body=body, idempotency_key=idempotency_key)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/wallet-transfers/{id}/")
