"""Official Python SDK for the AlphaPay payment aggregator API."""

from .client import AlphaPayClient
from .exceptions import (
    AlphaPayAuthenticationError,
    AlphaPayConnectionError,
    AlphaPayError,
    AlphaPayIdempotencyError,
    AlphaPayNotFoundError,
    AlphaPayPermissionError,
    AlphaPayRateLimitError,
    AlphaPayServerError,
    AlphaPayValidationError,
    AlphaPayWebhookSignatureError,
)
from .pagination import paginate
from .webhook import verify_signature

__version__ = "0.1.0"

__all__ = [
    "AlphaPayClient",
    "AlphaPayError",
    "AlphaPayAuthenticationError",
    "AlphaPayPermissionError",
    "AlphaPayNotFoundError",
    "AlphaPayValidationError",
    "AlphaPayRateLimitError",
    "AlphaPayServerError",
    "AlphaPayConnectionError",
    "AlphaPayIdempotencyError",
    "AlphaPayWebhookSignatureError",
    "verify_signature",
    "paginate",
    "__version__",
]
