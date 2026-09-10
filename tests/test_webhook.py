from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from alphapay import AlphaPayWebhookSignatureError, verify_signature  # noqa: E402

SECRET = "whsec_test"


def _sign(body: str, timestamp: int) -> str:
    return hmac.new(SECRET.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()


class WebhookTest(unittest.TestCase):
    def test_accepts_a_correctly_signed_fresh_payload_and_returns_the_parsed_event(self) -> None:
        body = json.dumps({"event": "payment.succeeded", "data": {"id": "tx_123"}})
        timestamp = int(time.time())

        event = verify_signature(body, _sign(body, timestamp), timestamp, SECRET)

        self.assertEqual(event, {"event": "payment.succeeded", "data": {"id": "tx_123"}})

    def test_rejects_a_payload_signed_with_the_wrong_secret(self) -> None:
        body = json.dumps({"event": "payment.succeeded", "data": {}})
        timestamp = int(time.time())
        wrong_signature = hmac.new(b"wrong_secret", f"{timestamp}.{body}".encode(), hashlib.sha256).hexdigest()

        with self.assertRaises(AlphaPayWebhookSignatureError):
            verify_signature(body, wrong_signature, timestamp, SECRET)

    def test_rejects_a_replayed_payload_outside_the_tolerance_window(self) -> None:
        body = json.dumps({"event": "payment.succeeded", "data": {}})
        stale_timestamp = int(time.time()) - 10_000

        with self.assertRaisesRegex(AlphaPayWebhookSignatureError, "tolérance"):
            verify_signature(body, _sign(body, stale_timestamp), stale_timestamp, SECRET)

    def test_rejects_a_tampered_body_even_if_the_signature_was_valid_for_the_original_body(self) -> None:
        original_body = json.dumps({"event": "payment.succeeded", "data": {"amount": "100"}})
        timestamp = int(time.time())
        signature = _sign(original_body, timestamp)
        tampered_body = json.dumps({"event": "payment.succeeded", "data": {"amount": "999999"}})

        with self.assertRaises(AlphaPayWebhookSignatureError):
            verify_signature(tampered_body, signature, timestamp, SECRET)


if __name__ == "__main__":
    unittest.main()
