from __future__ import annotations

import secrets
from typing import Any, Dict, Optional

from ..http import Http


class WebhookSubscriptionsResource:
    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/merchant-webhook-subscriptions/", query=params)

    def subscribe(self, webhook_id: str, event_type: str) -> Dict[str, Any]:
        """ATTENTION : dashboard-only -- 403 via clé API."""
        return self._http.request("POST", "/merchant-webhook-subscriptions/", body={"webhook": webhook_id, "event_type": event_type})

    def unsubscribe(self, subscription_id: str) -> None:
        """ATTENTION : dashboard-only -- 403 via clé API."""
        self._http.request("DELETE", f"/merchant-webhook-subscriptions/{subscription_id}/")


class WebhookLogsResource:
    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/webhook-logs/", query=params)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/webhook-logs/{id}/")

    def resend(self, id: str) -> Dict[str, Any]:
        """ATTENTION : dashboard-only -- 403 via clé API. Rejoue immédiatement
        cette livraison (nouvelle tentative hors du calendrier de retry automatique).
        """
        return self._http.request("POST", f"/webhook-logs/{id}/resend/")


class WebhookEndpointsResource:
    """Points de terminaison webhook du marchand (CRUD), abonnements par
    type d'événement (``.subscriptions``), et historique des livraisons
    (``.logs``). Pour vérifier la signature d'un webhook reçu, voir
    :func:`alphapay.webhook.verify_signature` (fonction à part, pas une
    méthode de cette ressource).

    Vérifié en conditions réelles : ``list``/``get`` (webhooks, abonnements,
    journal) fonctionnent bien via clé API -- mais toute écriture est
    dashboard-only (403, ``error_code == "dashboard_only"``) : ``create``,
    ``update``, ``rotate_secret``, ``delete``,
    ``subscriptions.subscribe()``/``unsubscribe()``, ``logs.resend()``.
    """

    def __init__(self, http: Http) -> None:
        self._http = http
        self.subscriptions = WebhookSubscriptionsResource(http)
        self.logs = WebhookLogsResource(http)

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/merchant-webhooks/", query=params)

    def create(self, *, url: str, environment: str, description: Optional[str] = None, signing_secret: Optional[str] = None) -> Dict[str, Any]:
        """ATTENTION : dashboard-only -- 403 via clé API.
        ``signing_secret`` n'est présent en clair dans la réponse qu'à la
        création (ou après :meth:`rotate_secret`) -- jamais récupérable ensuite.
        """
        body = {k: v for k, v in dict(url=url, description=description, environment=environment, signing_secret=signing_secret).items() if v is not None}
        return self._http.request("POST", "/merchant-webhooks/", body=body)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/merchant-webhooks/{id}/")

    def update(self, id: str, **params: Any) -> Dict[str, Any]:
        """ATTENTION : dashboard-only -- 403 via clé API."""
        return self._http.request("PATCH", f"/merchant-webhooks/{id}/", body=params)

    def rotate_secret(self, id: str) -> Dict[str, Any]:
        """ATTENTION : dashboard-only -- 403 via clé API.
        Génère et renvoie un nouveau secret -- l'ancien cesse immédiatement
        de valider les signatures. Le secret est généré ICI, côté SDK, et
        envoyé explicitement : un PATCH signing_secret vide ne régénère RIEN
        côté API une fois qu'un secret existe déjà (il ne s'auto-génère qu'à
        la création initiale) -- même constat que dans le dashboard AlphaPay
        (Webhooks.tsx.generateSigningSecret).
        """
        signing_secret = secrets.token_hex(32)
        return self._http.request("PATCH", f"/merchant-webhooks/{id}/", body={"signing_secret": signing_secret})

    def delete(self, id: str) -> None:
        """ATTENTION : dashboard-only -- 403 via clé API."""
        self._http.request("DELETE", f"/merchant-webhooks/{id}/")
