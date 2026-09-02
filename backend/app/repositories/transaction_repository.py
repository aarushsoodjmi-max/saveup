from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self.db.get(Transaction, transaction_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: UUID,
        *,
        offset: int,
        limit: int,
        goal_id: UUID | None = None,
        transaction_type: str | None = None,
    ) -> tuple[list[Transaction], int]:
        count_stmt = select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        list_stmt = select(Transaction).where(Transaction.user_id == user_id)

        if goal_id is not None:
            count_stmt = count_stmt.where(Transaction.goal_id == goal_id)
            list_stmt = list_stmt.where(Transaction.goal_id == goal_id)
        if transaction_type is not None:
            count_stmt = count_stmt.where(Transaction.transaction_type == transaction_type)
            list_stmt = list_stmt.where(Transaction.transaction_type == transaction_type)

        total = self.db.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
        rows = list(self.db.execute(list_stmt).scalars().all())
        return rows, total

    def search(
        self,
        *,
        offset: int,
        limit: int,
        user_id: UUID | None = None,
        goal_id: UUID | None = None,
        transaction_type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Transaction], int]:
        count_stmt = select(func.count()).select_from(Transaction)
        list_stmt = select(Transaction)

        for column, value in (
            (Transaction.user_id, user_id),
            (Transaction.goal_id, goal_id),
            (Transaction.transaction_type, transaction_type),
            (Transaction.status, status),
        ):
            if value is not None:
                count_stmt = count_stmt.where(column == value)
                list_stmt = list_stmt.where(column == value)

        total = self.db.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(Transaction.created_at.desc()).offset(offset).limit(limit)
        rows = list(self.db.execute(list_stmt).scalars().all())
        return rows, total

    def sum_by_type(self, transaction_type: str, status: str = "SUCCESS") -> float:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_type == transaction_type,
            Transaction.status == status,
        )
        return self.db.execute(stmt).scalar_one()
