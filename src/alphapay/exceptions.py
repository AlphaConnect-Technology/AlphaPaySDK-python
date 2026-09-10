"""
Toute erreur API passe par apps.core.renderers.StandardJSONRenderer côté
AlphaPayBack :
    {"success": false, "error": <forme variable>, "code": <statut HTTP>}
`error` n'a PAS une forme unique :
    - erreurs de validation DRF      -> {"champ": ["message", ...], ...}
    - erreurs métier personnalisées  -> {"message": "...", "code": "<code_machine>"}
    - erreurs d'authentification/permission -> {"detail": "..."}
str(exception) normalise ces trois formes en une seule chaîne lisible ;
`.raw` garde la forme originale pour qui a besoin du détail par champ.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class AlphaPayError(Exception):
    """Exception de base -- toutes les erreurs API en sont une sous-classe."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        error_code: Optional[str] = None,
        raw: Any = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        #: Code machine, quand l'API en fournit un (ex. "dashboard_only", "invalid_file_type") --
        #: absent sur les erreurs de validation par champ.
        self.error_code = error_code
        #: Corps d'erreur brut, tel que renvoyé par l'API.
        self.raw = raw
        #: Présent uniquement sur une erreur de validation DRF ({"champ": [...]}).
        self.field_errors = field_errors
        self.request_id = request_id


class AlphaPayAuthenticationError(AlphaPayError):
    pass


class AlphaPayPermissionError(AlphaPayError):
    pass


class AlphaPayNotFoundError(AlphaPayError):
    pass


class AlphaPayValidationError(AlphaPayError):
    pass


class AlphaPayRateLimitError(AlphaPayError):
    """429 -- `retry_after` (secondes) est renseigné quand l'API précise un header Retry-After."""

    def __init__(self, message: str, *, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AlphaPayServerError(AlphaPayError):
    pass


class AlphaPayConnectionError(AlphaPayError):
    """Connexion/DNS/timeout -- jamais atteint le serveur AlphaPay, `status` vaut 0."""

    pass


class AlphaPayIdempotencyError(AlphaPayError):
    """409 -- Idempotency-Key réutilisée avec un payload différent (cf. apps.core.mixins.IdempotencyMixin côté API)."""

    pass


class AlphaPayWebhookSignatureError(Exception):
    """Levée par alphapay.webhook.verify_signature() -- signature invalide ou timestamp hors fenêtre de tolérance (rejeu)."""

    pass


def error_from_response(status: int, body: Any, request_id: Optional[str] = None) -> AlphaPayError:
    """Construit l'exception normalisée à partir de la réponse HTTP. `body` est
    déjà le contenu de la clé "error" de l'enveloppe (pas l'enveloppe entière).
    """
    message, error_code, field_errors = _interpret_error_body(body)

    kwargs = dict(status=status, error_code=error_code, raw=body, field_errors=field_errors, request_id=request_id)

    if status == 401:
        return AlphaPayAuthenticationError(message, **kwargs)
    if status == 403:
        return AlphaPayPermissionError(message, **kwargs)
    if status == 404:
        return AlphaPayNotFoundError(message, **kwargs)
    if status == 409:
        return AlphaPayIdempotencyError(message, **kwargs)
    if status == 429:
        return AlphaPayRateLimitError(message, **kwargs)
    if status in (400, 422):
        return AlphaPayValidationError(message, **kwargs)
    if status >= 500:
        return AlphaPayServerError(message, **kwargs)
    return AlphaPayError(message, **kwargs)


def _interpret_error_body(body: Any):
    if body is None:
        return "Erreur AlphaPay inconnue.", None, None
    if isinstance(body, str):
        return body, None, None
    if isinstance(body, dict):
        # {"message": "...", "code": "..."} -- erreurs métier personnalisées.
        message = body.get("message")
        if isinstance(message, str):
            code = body.get("code")
            return message, code if isinstance(code, str) else None, None
        # {"detail": "..."} -- erreurs d'auth/permission DRF standard.
        detail = body.get("detail")
        if isinstance(detail, str):
            return detail, None, None
        # {"champ": ["erreur", ...], ...} -- erreurs de validation DRF.
        field_errors = {
            field: value
            for field, value in body.items()
            if isinstance(field, str) and isinstance(value, list) and value and all(isinstance(v, str) for v in value)
        }
        if field_errors:
            summary = " — ".join(f"{field}: {', '.join(errors)}" for field, errors in field_errors.items())
            return summary, None, field_errors
    return "Erreur AlphaPay inconnue.", None, None
