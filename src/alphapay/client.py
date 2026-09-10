from __future__ import annotations

from typing import Optional

from .http import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, Http
from .resources.api_keys import ApiKeysResource
from .resources.balances import BalancesResource
from .resources.checkout_sessions import CheckoutSessionsResource
from .resources.customers import CustomersResource
from .resources.payment_links import PaymentLinksResource
from .resources.settlements import SettlementsResource
from .resources.transactions import TransactionsResource
from .resources.wallet_transfers import WalletTransfersResource
from .resources.webhook_endpoints import WebhookEndpointsResource


class AlphaPayClient:
    """Client principal du SDK AlphaPay. Une instance = une clé API = un
    marchand + un environnement (live/sandbox, déduit automatiquement du
    préfixe de la clé -- ``sk_live_...`` ou ``sk_test_...``).

    :Example:

    >>> alphapay = AlphaPayClient(os.environ["ALPHAPAY_SECRET_KEY"])
    >>> payment = alphapay.transactions.payin_initialize(
    ...     amount=5000,
    ...     currency="XOF",
    ...     country="BJ",
    ...     network="MTN_BJ",
    ...     customer={"phone": "+22900000000", "full_name": "Client Test"},
    ...     idempotency_key=True,
    ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        #: Client HTTP bas niveau -- nécessaire à :func:`alphapay.pagination.paginate`
        #: pour suivre un lien "next" (URL absolue renvoyée par l'API), pas
        #: destiné à un usage direct en dehors de ce cas.
        self.http = Http(api_key, base_url, timeout, max_retries)
        self.environment = self.http.environment

        self.transactions = TransactionsResource(self.http)
        self.payment_links = PaymentLinksResource(self.http)
        self.checkout_sessions = CheckoutSessionsResource(self.http)
        self.customers = CustomersResource(self.http)
        self.settlements = SettlementsResource(self.http)
        self.wallet_transfers = WalletTransfersResource(self.http)
        self.balances = BalancesResource(self.http)
        self.api_keys = ApiKeysResource(self.http)
        self.webhook_endpoints = WebhookEndpointsResource(self.http)
