"""Payment gateway abstraction (mock).

Mirrors the shape of a real gateway integration (Razorpay/Stripe-style):
create an order server-side, hand the client an order id to complete
checkout with, then trust only a signature-verified webhook (or a
verify-call whose signature checks out) to actually move money.

Swapping to a real provider means writing a new class that implements
:class:`PaymentProvider` and pointing ``payment_provider`` at it --
``PaymentService`` never touches gateway specifics directly.
"""

import hashlib
import hmac
from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import uuid4

from app.core.config import settings


class PaymentProvider(ABC):
    name: str

    @abstractmethod
    def create_order(self, *, amount: Decimal, currency: str, receipt: str) -> str:
        """Returns a provider-side order id."""

    @abstractmethod
    def verify_signature(self, *, payload: str, signature: str) -> bool:
        """Verifies a webhook/callback signature against a raw payload string."""


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    def __init__(self, secret: str):
        self._secret = secret

    def create_order(self, *, amount: Decimal, currency: str, receipt: str) -> str:
        return f"mock_order_{uuid4().hex[:20]}"

    def sign(self, payload: str) -> str:
        """Only the mock provider needs to *generate* signatures --
        it stands in for the gateway on both sides of the wire during
        local testing. A real provider signs on its own servers.
        """
        return hmac.new(self._secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_signature(self, *, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)


payment_provider: PaymentProvider = MockPaymentProvider(secret=settings.payment_webhook_secret)
