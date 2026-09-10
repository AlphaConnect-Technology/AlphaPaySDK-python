"""Vérification de signature des webhooks AlphaPay."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Union

from .exceptions import AlphaPayWebhookSignatureError

#: Fenêtre de tolérance par défaut, en secondes -- même valeur que côté API
#: (apps.webhooks.services.SIGNATURE_TOLERANCE_SECONDS).
DEFAULT_TOLERANCE_SECONDS = 300


def verify_signature(
    payload: Union[str, bytes],
    signature: str,
    timestamp: Union[str, int],
    secret: str,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> Dict[str, Any]:
    """Vérifie qu'un webhook provient bien d'AlphaPay et n'a pas été rejoué.

    Reproduit exactement apps.webhooks.services.sign_payload côté API :
    HMAC-SHA256 de "<timestamp>.<corps>", comparé en temps constant
    (hmac.compare_digest) pour ne jamais fuiter d'information via le timing
    de la comparaison.

    :param payload: Corps BRUT de la requête (chaîne/bytes exacts reçus,
        avant tout json.loads -- la signature porte sur les octets exacts
        envoyés).
    :param signature: Valeur du header X-Webhook-Signature.
    :param timestamp: Valeur du header X-Webhook-Timestamp.
    :param secret: Secret de signature du webhook (visible une seule fois à
        la création/rotation dans le dashboard AlphaPay).
    :param tolerance_seconds: Fenêtre d'acceptation en secondes (défaut 300,
        comme recommandé par l'API).
    :returns: L'événement décodé (``{"event": ..., "data": ...}``) -- jamais
        renvoyé avant vérification de la signature. N'appelez jamais
        ``json.loads(payload)`` vous-même avant ce contrôle : ce serait
        traiter un webhook non authentifié.
    :raises AlphaPayWebhookSignatureError: si la signature est invalide ou le
        timestamp hors fenêtre de tolérance (rejeu).
    """
    try:
        ts = int(timestamp)
    except (TypeError, ValueError) as exc:
        raise AlphaPayWebhookSignatureError(f'Timestamp de webhook invalide : "{timestamp}".') from exc

    raw_body = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    signed_message = f"{ts}.".encode("utf-8") + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise AlphaPayWebhookSignatureError("Signature de webhook invalide — vérifiez le secret utilisé.")

    age_seconds = abs(time.time() - ts)
    if age_seconds > tolerance_seconds:
        raise AlphaPayWebhookSignatureError(
            f"Timestamp de webhook hors fenêtre de tolérance ({int(age_seconds)}s, limite {tolerance_seconds}s) — rejeu potentiel."
        )

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise AlphaPayWebhookSignatureError("Corps de webhook signé valide mais illisible (JSON invalide).") from exc

    if not isinstance(event, dict):
        raise AlphaPayWebhookSignatureError("Corps de webhook signé valide mais de forme inattendue (pas un objet JSON).")

    return event
