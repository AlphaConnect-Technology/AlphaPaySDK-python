from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

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
        require_phone: Optional[bool] = None,
        facebook_pixel_id: Optional[str] = None,
        google_ads_id: Optional[str] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        show_confirmation_page: Optional[bool] = None,
        redirect_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """``custom_fields`` : liste de ``{"key": str, "label": str, "required"?: bool}``,
        collectés sur la page publique du lien (cf. :meth:`create_public_checkout`).
        ``redirect_url`` devient obligatoire dès que ``show_confirmation_page=False``
        (bascule "page de confirmation" vs "redirection", cf. validation API).
        """
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
                require_phone=require_phone,
                facebook_pixel_id=facebook_pixel_id,
                google_ads_id=google_ads_id,
                custom_fields=custom_fields,
                show_confirmation_page=show_confirmation_page,
                redirect_url=redirect_url,
            ).items()
            if v is not None
        }
        return self._http.request("POST", "/payment-links/", body=body)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/payment-links/{id}/")

    def update(self, id: str, **params: Any) -> Dict[str, Any]:
        """Accepte les mêmes champs que :meth:`create`, tous optionnels (PATCH partiel)."""
        return self._http.request("PATCH", f"/payment-links/{id}/", body=params)

    def delete(self, id: str) -> None:
        self._http.request("DELETE", f"/payment-links/{id}/")

    def get_public(self, slug: str) -> Dict[str, Any]:
        """Consultation publique (page de paiement du lien) -- pas d'auth marchand,
        ``slug`` fait office de capacité. Utile pour prévisualiser son propre
        lien, mais surtout destiné à un front public (jamais la clé secrète
        côté client).
        """
        return self._http.request("GET", f"/payment-links/public/{slug}/")

    def create_public_checkout(
        self,
        slug: str,
        *,
        customer: Dict[str, Any],
        amount: Union[int, float, str, None] = None,
        custom_field_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Crée une CheckoutSession one-shot à partir du lien (montant + identité
        client) -- un lien étant réutilisable, chaque appel en crée une NOUVELLE.
        Ni pays ni réseau ici : ça se choisit ensuite sur la page checkout,
        pilotable avec le SDK checkout public (mobile/web) via le ``slug`` renvoyé.

        ``customer`` -- ``email``/``first_name``/``last_name`` requis, ``phone``
        requis seulement si le lien a ``require_phone=True`` (cf. :meth:`get_public`).
        ``amount`` requis si le lien est à montant libre (``amount_type: "FREE"``).

        Retourne ``{"slug", "checkout_url"}``.
        """
        body = {
            k: v
            for k, v in dict(customer=customer, amount=amount, custom_field_values=custom_field_values).items()
            if v is not None
        }
        return self._http.request("POST", f"/payment-links/public/{slug}/checkout/", body=body)
