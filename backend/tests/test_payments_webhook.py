"""Payment order creation + idempotent, signature-verified webhook."""

from decimal import Decimal

from app.models.goal import Goal
from app.services.payment_provider import payment_provider


def _create_goal(db_session, user, target="500.00"):
    goal = Goal(
        user_id=user.id,
        title="Webhook Goal",
        category="General",
        target_amount=Decimal(target),
        lock_type="EASY",
        status="ACTIVE",
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


def _sign(payload: dict) -> str:
    import json

    canonical = json.dumps(payload, sort_keys=True, default=str)
    return payment_provider.sign(canonical)


def test_create_payment_order(client, make_user, auth_headers, db_session):
    user = make_user()
    goal = _create_goal(db_session, user)

    response = client.post(
        "/api/v1/payments/create-order",
        json={"goal_id": str(goal.id), "amount": "100.00"},
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CREATED"
    assert body["provider_order_id"].startswith("mock_order_")


def test_webhook_rejects_invalid_signature(client, make_user, db_session):
    user = make_user()
    goal = _create_goal(db_session, user)

    from app.services.payment_service import PaymentService

    order = PaymentService(db_session).create_order(
        user=user, goal_id=goal.id, amount=Decimal("50.00"), idempotency_key=None
    )

    response = client.post(
        "/api/v1/payments/webhook",
        json={
            "event": "payment.captured",
            "provider_order_id": order.provider_order_id,
            "provider_payment_id": "pay_fake",
            "signature": "not-a-real-signature",
            "status": "SUCCESS",
        },
    )
    assert response.status_code == 401


def test_webhook_success_moves_money_exactly_once_even_if_redelivered(client, make_user, db_session):
    from app.services.payment_service import PaymentService

    user = make_user()
    goal = _create_goal(db_session, user)

    order = PaymentService(db_session).create_order(
        user=user, goal_id=goal.id, amount=Decimal("75.00"), idempotency_key=None
    )

    webhook_body = {
        "event": "payment.captured",
        "provider_order_id": order.provider_order_id,
        "provider_payment_id": "pay_12345",
        "status": "SUCCESS",
    }
    webhook_body["signature"] = _sign(webhook_body)

    first = client.post("/api/v1/payments/webhook", json=webhook_body)
    assert first.status_code == 200
    assert first.json()["status"] == "SUCCESS"

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("75.00")

    # Simulate the gateway redelivering the exact same webhook.
    second = client.post("/api/v1/payments/webhook", json=webhook_body)
    assert second.status_code == 200

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("75.00")  # unchanged -- not double-applied


def test_webhook_failure_marks_order_failed_without_moving_money(client, make_user, db_session):
    from app.services.payment_service import PaymentService

    user = make_user()
    goal = _create_goal(db_session, user)
    order = PaymentService(db_session).create_order(
        user=user, goal_id=goal.id, amount=Decimal("20.00"), idempotency_key=None
    )

    webhook_body = {
        "event": "payment.failed",
        "provider_order_id": order.provider_order_id,
        "provider_payment_id": "pay_failed",
        "status": "FAILED",
    }
    webhook_body["signature"] = _sign(webhook_body)

    response = client.post("/api/v1/payments/webhook", json=webhook_body)
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"

    db_session.refresh(goal)
    assert goal.saved_amount == Decimal("0.00")
