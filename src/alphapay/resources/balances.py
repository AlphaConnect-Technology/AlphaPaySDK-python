from __future__ import annotations

from typing import Any, Dict

from ..http import Http


class BalancesResource:
    """Soldes par pays/devise et grand livre des mouvements -- lecture seule
    (les mouvements naissent des autres ressources : transactions,
    reversements, transferts).
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/merchant-balances/", query=params)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/merchant-balances/{id}/")

    def ledger_entries(self, **params: Any) -> Dict[str, Any]:
        """ATTENTION : inaccessible via clé API (contrairement à
        :meth:`list`/:meth:`get`, qui fonctionnent bien avec une clé --
        vérifié en conditions réelles) : lève systématiquement
        :class:`~alphapay.exceptions.AlphaPayPermissionError` (403,
        ``error_code == "dashboard_only"``). Le grand livre détaillé n'est
        consultable que depuis le dashboard (compte utilisateur).

        Filtres reconnus : ``page``, ``page_size``, ``country``,
        ``created_at__gte``, ``created_at__lte``.
        """
        return self._http.request("GET", "/merchant-ledger-entries/", query=params)
