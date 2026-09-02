from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import PaymentAttempt, PaymentOrder


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, order: PaymentOrder) -> PaymentOrder:
        self.db.add(order)
        self.db.flush()
        return order

    def get_order(self, order_id: UUID) -> PaymentOrder | None:
        return self.db.get(PaymentOrder, order_id)

    def get_order_locked(self, order_id: UUID) -> PaymentOrder | None:
        stmt = select(PaymentOrder).where(PaymentOrder.id == order_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_order_by_provider_id(self, provider_order_id: str) -> PaymentOrder | None:
        stmt = select(PaymentOrder).where(PaymentOrder.provider_order_id == provider_order_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_order_by_provider_id_locked(self, provider_order_id: str) -> PaymentOrder | None:
        stmt = (
            select(PaymentOrder)
            .where(PaymentOrder.provider_order_id == provider_order_id)
            .with_for_update()
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_order_by_idempotency_key(self, idempotency_key: str) -> PaymentOrder | None:
        stmt = select(PaymentOrder).where(PaymentOrder.idempotency_key == idempotency_key)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_attempt(self, attempt: PaymentAttempt) -> PaymentAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def list_attempts_for_order(self, order_id: UUID) -> list[PaymentAttempt]:
        stmt = (
            select(PaymentAttempt)
            .where(PaymentAttempt.payment_order_id == order_id)
            .order_by(PaymentAttempt.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def has_successful_attempt(self, order_id: UUID) -> bool:
        stmt = select(PaymentAttempt).where(
            PaymentAttempt.payment_order_id == order_id,
            PaymentAttempt.status == "SUCCESS",
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None
