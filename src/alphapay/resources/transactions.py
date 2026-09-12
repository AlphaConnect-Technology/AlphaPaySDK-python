from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..http import Http


class TransactionsResource:
    """Paiements (encaissements), retraits (payouts) et leur historique.

    Les méthodes ``payin_*``/``payout_*`` sont volontairement séparées du
    CRUD ``list``/``get`` -- ce sont des actions (initier un mouvement
    d'argent), pas des ressources REST classiques, cf. ``/payments/*`` et
    ``/payouts/*`` côté API.
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """PAS de ``page`` dans ``params`` -- ``TransactionListView`` est
        paginée par curseur côté API (``pagination_class =
        CreatedAtCursorPagination``), vérifié contre le code réel : ``page``
        n'a aucun effet ici, la réponse n'a pas de clé ``count``. Utilisez
        :func:`alphapay.pagination.paginate` pour tout parcourir, pas une
        boucle sur un numéro de page.

        Filtres reconnus : ``page_size``, ``search``, ``status``,
        ``transaction_type``, ``flow_direction``, ``country``, ``network``,
        ``customer``, ``created_at__gte``, ``created_at__lte``.
        """
        return self._http.request("GET", "/transactions/", query=params)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/transactions/{id}/")

    def download_invoice(self, id: str) -> Dict[str, Any]:
        """Télécharge la facture PDF -- réponse binaire authentifiée, 409
        hors INBOUND+SUCCESS (cf.
        ``apps.transactions.services.invoice.generate_invoice_pdf``).
        Retourne ``{"data": bytes, "content_type": str, "filename": str}``.
        """
        return self._http.request_binary(f"/transactions/{id}/invoice/")

    def export(self, **params: Any) -> Dict[str, Any]:
        """Export CSV -- mêmes filtres que :meth:`list`, sans limite de
        lignes ni pagination.
        """
        from urllib.parse import urlencode

        filtered = {k: v for k, v in params.items() if v is not None}
        qs = urlencode(filtered)
        return self._http.request_binary(f"/transactions/export/{'?' + qs if qs else ''}")

    def payin_initialize(
        self,
        *,
        amount: Union[int, float, str],
        currency: str,
        country: str,
        customer: Dict[str, Any],
        network: str,
        merchant: Optional[str] = None,
        description: Optional[str] = None,
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fee_charge_mode: Optional[str] = None,
        preferred_gateway: Optional[str] = None,
        otp: Optional[str] = None,
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        """Encaisse directement (push USSD/mobile money) sans page de
        checkout à suivre. ``idempotency_key`` fortement recommandée : un
        doublon pousse un second prompt de paiement vers le client final.

        ``customer`` -- cf. ``SoftpayCustomerSerializer`` : ``email``,
        ``first_name``, ``last_name`` et ``phone`` sont tous les 4
        OBLIGATOIRES (pas de page hébergée où le client les saisirait
        lui-même après coup). Il n'y a PAS de champ ``full_name`` côté API.

        Retourne ``{"message", "id", "status", "checkout_url", "instructions"}``
        -- PAS une transaction complète.
        """
        body = _drop_none(
            merchant=merchant,
            amount=amount,
            currency=currency,
            country=country,
            description=description,
            customer=customer,
            network=network,
            return_url=return_url,
            metadata=metadata,
            fee_charge_mode=fee_charge_mode,
            preferred_gateway=preferred_gateway,
            otp=otp,
        )
        return self._http.request("POST", "/payments/softpay/", body=body, idempotency_key=idempotency_key)

    def payin_verify(self, payment_id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/payments/{payment_id}/verify/")

    def payin_retry(
        self, payment_id: str, *, preferred_gateway: Optional[str] = None, idempotency_key: Union[str, bool, None] = None
    ) -> Dict[str, Any]:
        body = _drop_none(preferred_gateway=preferred_gateway)
        return self._http.request("POST", f"/payments/{payment_id}/retry/", body=body, idempotency_key=idempotency_key)

    def payin_confirm_otp(self, payment_id: str, otp: str) -> Dict[str, Any]:
        """Réseaux exigeant une confirmation en 2 temps (ex. Wizall Sénégal, Coris Bénin)."""
        return self._http.request("POST", f"/payments/{payment_id}/confirm-otp/", body={"otp": otp})

    def payout_initialize(
        self,
        *,
        amount: Union[int, float, str],
        currency: str,
        country: str,
        customer: Dict[str, Any],
        method: str,
        recipient: Dict[str, Any],
        merchant: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fee_charge_mode: Optional[str] = None,
        preferred_gateway: Optional[str] = None,
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        """Déclenche un retrait -- débite immédiatement le wallet marchand
        (réservation de solde). ``idempotency_key`` fortement recommandée :
        sans elle, un doublon débite deux fois le MÊME wallet.

        ``customer`` -- cf. ``CustomerCheckoutSerializer`` : ``email``,
        ``first_name``, ``last_name`` requis, ``phone`` optionnel (pas de
        champ ``full_name``). ``recipient`` -- cf. ``RecipientSerializer`` :
        UN SEUL champ, ``{"msisdn": "..."}`` -- c'est ``method`` qui porte le
        réseau/la banque, pas ``recipient``.

        Retourne ``{"message", "id"}``.
        """
        body = _drop_none(
            merchant=merchant,
            amount=amount,
            currency=currency,
            country=country,
            description=description,
            customer=customer,
            metadata=metadata,
            method=method,
            recipient=recipient,
            fee_charge_mode=fee_charge_mode,
            preferred_gateway=preferred_gateway,
        )
        return self._http.request("POST", "/payouts/initialize/", body=body, idempotency_key=idempotency_key)

    def payout_verify(self, payout_id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/payouts/{payout_id}/verify/")


def _drop_none(**kwargs: Any) -> Dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}
