from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from alphapay import AlphaPayClient, AlphaPayRateLimitError, AlphaPayValidationError  # noqa: E402
from alphapay.pagination import paginate  # noqa: E402

from server import TestServer  # noqa: E402


class ClientTest(unittest.TestCase):
    server: TestServer
    base_url: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = TestServer()
        cls.base_url = cls.server.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.__exit__(None, None, None)

    def setUp(self) -> None:
        self.server.reset()

    def test_detects_sandbox_vs_live_environment_from_key_prefix(self) -> None:
        sandbox = AlphaPayClient("sk_test_abc", self.base_url)
        live = AlphaPayClient("sk_live_abc", self.base_url)
        self.assertEqual(sandbox.environment, "sandbox")
        self.assertEqual(live.environment, "live")

    def test_unwraps_the_envelope_and_returns_data(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        tx = client.transactions.get("tx_1")
        self.assertEqual(tx, {"id": "tx_1", "reference": "REF1"})

    def test_reads_public_payment_link_options(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        link = client.payment_links.get_public("demo-slug")
        self.assertEqual(link["facebook_pixel_id"], "123456789012345")
        self.assertEqual(link["google_ads_id"], "AW-123456789")
        self.assertEqual(
            link["custom_fields"], [{"key": "reference_client", "label": "Référence client", "required": True}]
        )

    def test_sends_payment_link_tracking_and_custom_fields(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        link = client.payment_links.create(
            name="Lien de test",
            amount_type="FIXED",
            amount=5000,
            currency="XOF",
            facebook_pixel_id="123456789012345",
            google_ads_id="AW-123456789",
            custom_fields=[{"key": "reference_client", "label": "Référence client", "required": True}],
        )
        self.assertEqual(link["facebook_pixel_id"], "123456789012345")
        self.assertEqual(link["google_ads_id"], "AW-123456789")
        self.assertEqual(link["custom_fields"][0]["key"], "reference_client")

    def test_creates_checkout_from_public_payment_link(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        result = client.payment_links.create_public_checkout(
            "demo-slug",
            customer={"email": "client@example.com", "first_name": "Client", "last_name": "Test"},
            custom_field_values={"reference_client": "CMD-42"},
        )
        self.assertEqual(result["slug"], "checkout-slug")
        self.assertEqual(result["received"]["custom_field_values"]["reference_client"], "CMD-42")

    def test_maps_a_400_field_validation_error(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        with self.assertRaises(AlphaPayValidationError) as ctx:
            client.settlements.create(country="BJ", requested_amount=100, payout_method="x")
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.field_errors, {"amount": ["Ce champ est requis."]})

    def test_retries_a_429_honoring_retry_after_then_resolves(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url, max_retries=2)
        result = client.http.request("GET", "/retry-then-success/")
        self.assertEqual(result, {"id": "ok"})

    def test_gives_up_after_exhausting_retries(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url, max_retries=1)
        with self.assertRaises(AlphaPayRateLimitError):
            client.http.request("GET", "/always-429/")

    def test_sends_a_generated_idempotency_key_when_requested(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        result = client.http.request("POST", "/echo-headers/", body={}, idempotency_key=True)
        self.assertTrue(result["idempotency_key"])

    def test_paginate_follows_the_cursor_based_next_link(self) -> None:
        client = AlphaPayClient("sk_test_abc", self.base_url)
        collected = list(paginate(client.http, client.transactions.list()))
        self.assertEqual(collected, [{"id": "tx_1"}, {"id": "tx_2"}])


if __name__ == "__main__":
    unittest.main()
