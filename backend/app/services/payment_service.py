"""Deposit-via-payment-gateway workflow: create an order, then trust
only a signature-verified webhook to actually move money.

The webhook handler is the second-most safety-critical path in the
app after the ledger itself, so it follows the same rules: row-lock
first, one atomic commit, idempotent under duplicate delivery.
"""

import json
import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.models.payment import PaymentAttempt, PaymentOrder
from app.models.user import User
from app.repositories.goal_repository import GoalRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payment import PaymentWebhookPayload
from app.services.achievement_service import AchievementService
from app.services.ledger_service import LedgerService
from app.services.notification_service import NotificationService
from app.services.payment_provider import PaymentProvider, payment_provider as default_provider
from app.services.streak_service import StreakService

logger = logging.getLogger("saveup.payments")


def _canonical_payload(payload: PaymentWebhookPayload) -> str:
    """A stable, order-independent string to sign/verify -- excludes
    the signature field itself.
    """
    data = payload.model_dump(exclude={"signature"})
    return json.dumps(data, sort_keys=True, default=str)


class PaymentService:
    def __init__(self, db: Session, provider: PaymentProvider = default_provider):
        self.db = db
        self.provider = provider
        self.payment_repo = PaymentRepository(db)
        self.goal_repo = GoalRepository(db)
        self.ledger_service = LedgerService(db)

    def create_order(
        self, *, user: User, goal_id: UUID, amount: Decimal, idempotency_key: str | None
    ) -> PaymentOrder:
        if idempotency_key:
            existing = self.payment_repo.get_order_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing

        goal = self.goal_repo.get_for_user(goal_id, user.id)
        if goal is None:
            raise NotFoundError("Goal not found")
        if goal.status != "ACTIVE":
            raise ConflictError(f"Cannot create a payment order for a goal with status {goal.status}")

        provider_order_id = self.provider.create_order(
            amount=amount, currency="INR", receipt=f"goal:{goal_id}"
        )

        order = PaymentOrder(
            user_id=user.id,
            goal_id=goal_id,
            amount=amount,
            currency="INR",
            provider=self.provider.name,
            provider_order_id=provider_order_id,
            status="CREATED",
            idempotency_key=idempotency_key,
        )
        try:
            self.payment_repo.create_order(order)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if idempotency_key:
                existing = self.payment_repo.get_order_by_idempotency_key(idempotency_key)
                if existing is not None:
                    return existing
            raise ConflictError("A payment order for this request already exists") from None

        self.db.refresh(order)
        return order

    def get_order_for_user(self, order_id: UUID, user: User) -> PaymentOrder:
        order = self.payment_repo.get_order(order_id)
        if order is None or order.user_id != user.id:
            raise NotFoundError("Payment order not found")
        return order

    # ------------------------------------------------------------------
    def process_webhook(self, payload: PaymentWebhookPayload) -> PaymentAttempt:
        canonical = _canonical_payload(payload)
        if not self.provider.verify_signature(payload=canonical, signature=payload.signature):
            raise UnauthorizedError("Invalid webhook signature")

        order = self.payment_repo.get_order_by_provider_id_locked(payload.provider_order_id)
        if order is None:
            raise NotFoundError("Payment order not found for provider_order_id")

        # Idempotent under duplicate webhook delivery: if this order has
        # already reached a terminal state, just log the redelivery as
        # an attempt row and return -- no further money movement.
        if order.status in ("PAID", "FAILED", "EXPIRED"):
            attempt = PaymentAttempt(
                payment_order_id=order.id,
                provider_payment_id=payload.provider_payment_id,
                status="SUCCESS" if order.status == "PAID" else "FAILED",
                signature=payload.signature,
                signature_valid=True,
                raw_payload=canonical,
            )
            self.payment_repo.create_attempt(attempt)
            self.db.commit()
            self.db.refresh(attempt)
            return attempt

        if payload.status.upper() != "SUCCESS":
            attempt = PaymentAttempt(
                payment_order_id=order.id,
                provider_payment_id=payload.provider_payment_id,
                status="FAILED",
                signature=payload.signature,
                signature_valid=True,
                failure_reason=f"Provider reported status={payload.status}",
                raw_payload=canonical,
            )
            self.payment_repo.create_attempt(attempt)
            order.status = "FAILED"
            self.db.commit()
            self.db.refresh(attempt)
            return attempt

        # --- Successful payment: move money atomically with the order update ---
        goal = self.goal_repo.get_locked(order.goal_id)
        if goal is None:
            raise NotFoundError("Goal not found for this payment order")

        idempotency_key = f"payment_order:{order.id}"
        transaction = self.ledger_service.apply_deposit_locked(
            goal=goal,
            user_id=order.user_id,
            amount=order.amount,
            reference_type="payment_order",
            reference_id=order.id,
            idempotency_key=idempotency_key,
            metadata={"provider_payment_id": payload.provider_payment_id},
        )

        attempt = PaymentAttempt(
            payment_order_id=order.id,
            provider_payment_id=payload.provider_payment_id,
            status="SUCCESS",
            signature=payload.signature,
            signature_valid=True,
            raw_payload=canonical,
        )
        self.payment_repo.create_attempt(attempt)

        order.status = "PAID"
        order.transaction_id = transaction.id

        try:
            self.db.commit()
        except IntegrityError:
            # Extremely narrow race: a concurrent delivery already
            # inserted a transaction with this idempotency_key between
            # our check and our commit. Roll back this attempt's write
            # and let the already-committed one stand.
            self.db.rollback()
            logger.warning("Duplicate webhook delivery detected for order %s", order.id)
            existing = self.ledger_service.transaction_repo.get_by_idempotency_key(idempotency_key)
            order = self.payment_repo.get_order(order.id)
            if existing is not None and order is not None and order.status != "PAID":
                order.status = "PAID"
                order.transaction_id = existing.id
                self.db.commit()
            attempt = PaymentAttempt(
                payment_order_id=order.id if order else None,
                provider_payment_id=payload.provider_payment_id,
                status="SUCCESS",
                signature=payload.signature,
                signature_valid=True,
                raw_payload=canonical,
            )
            self.payment_repo.create_attempt(attempt)
            self.db.commit()
            self.db.refresh(attempt)
            return attempt

        self.db.refresh(attempt)

        # --- Best-effort follow-ups (each commits/rolls back on its own) ---
        user = UserRepository(self.db).get_by_id(order.user_id)
        if user is not None:
            notification_service = NotificationService(self.db)
            notification_service.notify_deposit(
                user_id=order.user_id, goal_title=goal.title, amount=order.amount
            )
            if goal.status == "COMPLETED":
                notification_service.notify_goal_completed(user_id=order.user_id, goal_title=goal.title)
            StreakService(self.db).record_deposit(order.user_id)
            AchievementService(self.db, notification_service).evaluate_and_unlock_for_user(order.user_id)

        return attempt
