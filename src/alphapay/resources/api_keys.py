from __future__ import annotations

from typing import Any, Dict, Optional

from ..http import Http


class IpWhitelistResource:
    """Whitelist IP requise pour les payouts -- partagée par toutes les
    clés du marchand (cf. ``apps.api_keys.models.MerchantIpWhitelistEntry``
    côté API). Fonctionne bien via clé API -- vérifié en conditions réelles.
    """

    def __init__(self, http: Http) -> None:
        self._http = http

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/merchant-ip-whitelist/", query=params)

    def create(self, *, ip_address: str, label: Optional[str] = None) -> Dict[str, Any]:
        body = {k: v for k, v in dict(ip_address=ip_address, label=label).items() if v is not None}
        return self._http.request("POST", "/merchant-ip-whitelist/", body=body)

    def update(self, id: str, **params: Any) -> Dict[str, Any]:
        return self._http.request("PATCH", f"/merchant-ip-whitelist/{id}/", body=params)

    def delete(self, id: str) -> None:
        self._http.request("DELETE", f"/merchant-ip-whitelist/{id}/")


class ApiKeysResource:
    """Gestion des clés API du marchand, et whitelist IP (via ``.ip_whitelist``).

    ATTENTION : ``list``/``create``/``get``/``revoke``/``delete``
    ci-dessous sont entièrement inaccessibles via clé API (403,
    ``error_code == "dashboard_only"``, vérifié en conditions réelles) --
    cohérent avec la sécurité attendue : une clé compromise ne doit pas
    pouvoir créer d'autres clés pour elle-même ni lister les clés
    existantes. Seul ``.ip_whitelist`` fonctionne via clé API.
    """

    def __init__(self, http: Http) -> None:
        self._http = http
        self.ip_whitelist = IpWhitelistResource(http)

    def list(self, **params: Any) -> Dict[str, Any]:
        return self._http.request("GET", "/merchant-api-keys/", query=params)

    def create(self, *, environment: str, name: Optional[str] = None, scope: Optional[str] = None, expires_at: Optional[str] = None) -> Dict[str, Any]:
        """``secret`` n'est présent QUE dans cette réponse -- jamais
        récupérable ensuite, à stocker immédiatement côté appelant.
        """
        body = {k: v for k, v in dict(name=name, environment=environment, scope=scope, expires_at=expires_at).items() if v is not None}
        return self._http.request("POST", "/merchant-api-keys/", body=body)

    def get(self, id: str) -> Dict[str, Any]:
        return self._http.request("GET", f"/merchant-api-keys/{id}/")

    def revoke(self, id: str) -> Dict[str, Any]:
        return self._http.request("POST", f"/merchant-api-keys/{id}/revoke/")

    def delete(self, id: str) -> None:
        self._http.request("DELETE", f"/merchant-api-keys/{id}/")
