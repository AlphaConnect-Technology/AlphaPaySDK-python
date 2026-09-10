from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..http import Http


class CheckoutSessionsResource:
    """Sessions de checkout à usage unique -- chacune génère sa propre page
    de paiement hébergée (``checkout_url``), pré-remplie pour un client
    précis. Contrairement à un lien de paiement réutilisable, une session
    correspond à UNE tentative de paiement.
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        """Filtres reconnus : ``page``, ``page_size``, ``search``, ``status``."""
        return self._http.request("GET", "/checkout-sessions/", query=params)

    def create(
        self,
        *,
        amount: Union[int, float, str],
        currency: str,
        customer_email: str,
        customer_name: str,
        description: Optional[str] = None,
        country: Optional[str] = None,
        customer_phone: Optional[str] = None,
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Union[str, bool, None] = None,
    ) -> Dict[str, Any]:
        body = {
            k: v
            for k, v in dict(
                amount=amount,
                currency=currency,
                description=description,
                country=country,
                customer_email=customer_email,
                customer_name=customer_name,
                customer_phone=customer_phone,
                return_url=return_url,
                metadata=metadata,
            ).items()
            if v is not None
        }
        return self._http.request("POST", "/checkout-sessions/", body=body, idempotency_key=idempotency_key)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/checkout-sessions/{id}/")

    def cancel(self, id: str) -> Dict[str, Any]:
        return self._http.request("POST", f"/checkout-sessions/{id}/cancel/")
