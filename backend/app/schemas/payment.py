from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentOrderRequest(BaseModel):
    goal_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)


class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    goal_id: UUID
    amount: Decimal
    currency: str
    provider: str
    provider_order_id: str
    status: str
    created_at: datetime


class VerifyPaymentRequest(BaseModel):
    """Client-side confirmation call, mirroring how real gateways return
    control to the client after checkout (e.g. Razorpay Checkout).
    The webhook is still the authoritative success signal; this endpoint
    only marks the attempt and, for the mock provider, can optionally
    finalize the payment immediately for local testing.
    """

    payment_order_id: UUID
    provider_payment_id: str
    signature: str


class PaymentWebhookPayload(BaseModel):
    event: str
    provider_order_id: str
    provider_payment_id: str
    signature: str
    status: str
