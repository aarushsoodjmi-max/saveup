from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, get_idempotency_key
from app.models.user import User
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    PaymentWebhookPayload,
    VerifyPaymentRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=PaymentOrderResponse, status_code=201)
def create_payment_order(
    payload: CreatePaymentOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    return PaymentService(db).create_order(
        user=current_user,
        goal_id=payload.goal_id,
        amount=payload.amount,
        idempotency_key=idempotency_key,
    )


@router.post("/verify")
def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Client-side checkout-completion callback. Internally reuses the
    exact same signature-verified, idempotent code path as the webhook
    (:meth:`PaymentService.process_webhook`) so a deposit can never be
    double-applied regardless of whether it arrives via this endpoint,
    the webhook, or both (duplicate delivery is common with real
    gateways).
    """
    service = PaymentService(db)
    order = service.get_order_for_user(payload.payment_order_id, current_user)
    webhook_payload = PaymentWebhookPayload(
        event="payment.captured",
        provider_order_id=order.provider_order_id,
        provider_payment_id=payload.provider_payment_id,
        signature=payload.signature,
        status="SUCCESS",
    )
    attempt = service.process_webhook(webhook_payload)
    return {"status": attempt.status, "payment_order_id": str(order.id)}


@router.post("/webhook")
def payment_webhook(payload: PaymentWebhookPayload, db: Session = Depends(get_db)):
    """Called by the payment gateway itself -- deliberately unauthenticated
    (no user JWT available), trust is established entirely via
    ``payload.signature``.
    """
    attempt = PaymentService(db).process_webhook(payload)
    return {"status": attempt.status}


@router.get("/orders/{order_id}", response_model=PaymentOrderResponse)
def get_payment_order(
    order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return PaymentService(db).get_order_for_user(order_id, current_user)
