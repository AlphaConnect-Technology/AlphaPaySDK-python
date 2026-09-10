from __future__ import annotations

from typing import Any, Dict, Union

from ..http import Http


class SettlementsResource:
    """Reversements (retraits vers un compte bancaire ou mobile money
    enregistré) -- cf. :class:`WalletTransfersResource` pour un transfert
    entre wallets AlphaPay.

    ATTENTION : entièrement inaccessible via clé API (``sk_live_...``/``sk_test_...``),
    y compris en LECTURE -- toutes les méthodes de cette ressource lèvent
    systématiquement une :class:`~alphapay.exceptions.AlphaPayPermissionError`
    (403, ``error_code == "dashboard_only"``). Restriction volontaire côté
    API (``apps.core.mixins.forbid_api_key``, vérifiée contre le code réel
    ET contre une vraie clé live) : un retrait ne peut être déclenché ou
    consulté que par un compte utilisateur connecté au dashboard, jamais par
    une clé API -- même la vôtre. Cette ressource ne peut donc pas servir à
    une intégration serveur automatisée ; elle reste dans le SDK pour rester
    honnête sur la forme des endpoints, pas pour un usage réel avec ce client.
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``status``, ``country``."""
        return self._http.request("GET", "/settlements/", query=params)

    def create(
        self,
        *,
        country: str,
        requested_amount: Union[int, float, str],
        payout_method: str,
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        """Débite le solde disponible du pays concerné dès la création -- recommandé avec ``idempotency_key``."""
        body = {"country": country, "requested_amount": requested_amount, "payout_method": payout_method}
        return self._http.request("POST", "/settlements/", body=body, idempotency_key=idempotency_key)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/settlements/{id}/")

    def cancel(self, id: str) -> Dict[str, Any]:
        """Uniquement possible tant que le reversement est PENDING."""
        return self._http.request("POST", f"/settlements/{id}/cancel/")
