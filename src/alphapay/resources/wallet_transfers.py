from __future__ import annotations

from typing import Any, Dict, Union

from ..http import Http


class WalletTransfersResource:
    """Transferts entre les wallets multi-pays d'un même marchand (avec
    conversion automatique si les devises diffèrent). L'argent ne quitte
    jamais la plateforme -- usage typique : approvisionner le wallet du pays
    d'un bénéficiaire avant un payout Mobile Money.

    Accessible via clé API depuis le 2026-09-24 (auparavant 403
    ``dashboard_only``) :

    - :meth:`create` exige une clé de scope ``PAYOUT`` ou ``BOTH`` -- une clé
      ``PAYIN`` reçoit un :class:`~alphapay.AlphaPayPermissionError`,
      ``error_code == "api_key_scope_forbidden"``.
    - :meth:`list` / :meth:`get` : toute clé du marchand.

    Cycle de vie (``STATUS_*``) : ``PENDING`` -> ``COMPLETED`` ou ``REJECTED``.
    Un transfert n'est ``COMPLETED`` immédiatement que si l'auto-approbation
    est activée pour le marchand (réglage AlphaPay, ``auto_approved_via`` =
    ``"GLOBAL"``/``"MERCHANT"``) ; sinon il reste ``PENDING`` jusqu'à
    validation par un admin AlphaPay -- suivez les webhooks
    ``wallet_transfer.completed``/``.rejected`` plutôt que d'interroger
    :meth:`get` en boucle.

    Frais : prélevés sur le montant CONVERTI -- ``to_amount`` est déjà net,
    ``fee_amount``/``fee_percent_applied`` détaillent le frais retenu.
    """

    STATUS_PENDING = "PENDING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_REJECTED = "REJECTED"

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``status``,
        ``from_country``, ``to_country`` (codes ISO2, ex. ``"CM"``)."""
        return self._http.request("GET", "/wallet-transfers/", query=params)

    def create(
        self,
        *,
        from_country: str,
        to_country: str,
        from_amount: Union[int, float, str],
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        """Réserve ``from_amount`` sur le wallet source. ``idempotency_key``
        fortement recommandée (``True`` en génère une) : sans elle, un retry
        réseau réserverait deux fois le montant. Réutiliser une clé avec un
        contenu différent lève :class:`~alphapay.AlphaPayIdempotencyError` (409).

        Refus métier -> :class:`~alphapay.AlphaPayValidationError` (422),
        ``error_code`` : ``"same_country"``, ``"transfer_already_pending"``
        (un seul transfert ``PENDING`` à la fois par marchand),
        ``"wallet_frozen"``, ``"insufficient_balance"``.
        """
        body = {"from_country": from_country, "to_country": to_country, "from_amount": from_amount}
        return self._http.request("POST", "/wallet-transfers/", body=body, idempotency_key=idempotency_key)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/wallet-transfers/{id}/")
