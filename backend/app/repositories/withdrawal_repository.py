from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.withdrawal_request import WithdrawalRequest


class WithdrawalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, request: WithdrawalRequest) -> WithdrawalRequest:
        self.db.add(request)
        self.db.flush()
        return request

    def get_by_id(self, request_id: UUID) -> WithdrawalRequest | None:
        return self.db.get(WithdrawalRequest, request_id)

    def get_locked(self, request_id: UUID) -> WithdrawalRequest | None:
        stmt = select(WithdrawalRequest).where(WithdrawalRequest.id == request_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_for_user(self, request_id: UUID, user_id: UUID) -> WithdrawalRequest | None:
        stmt = select(WithdrawalRequest).where(
            WithdrawalRequest.id == request_id,
            WithdrawalRequest.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self, user_id: UUID, *, offset: int, limit: int
    ) -> tuple[list[WithdrawalRequest], int]:
        count_stmt = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.user_id == user_id
        )
        list_stmt = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.user_id == user_id)
            .order_by(WithdrawalRequest.requested_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total = self.db.execute(count_stmt).scalar_one()
        rows = list(self.db.execute(list_stmt).scalars().all())
        return rows, total

    def list_pending(self, *, offset: int, limit: int) -> tuple[list[WithdrawalRequest], int]:
        statuses = ("PENDING", "APPROVED", "COOLDOWN")
        count_stmt = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.status.in_(statuses)
        )
        list_stmt = (
            select(WithdrawalRequest)
            .where(WithdrawalRequest.status.in_(statuses))
            .order_by(WithdrawalRequest.requested_at.asc())
            .offset(offset)
            .limit(limit)
        )
        total = self.db.execute(count_stmt).scalar_one()
        rows = list(self.db.execute(list_stmt).scalars().all())
        return rows, total

    def count_pending(self) -> int:
        stmt = select(func.count()).select_from(WithdrawalRequest).where(
            WithdrawalRequest.status.in_(("PENDING", "APPROVED", "COOLDOWN"))
        )
        return self.db.execute(stmt).scalar_one()

    def get_open_for_goal(self, goal_id: UUID) -> WithdrawalRequest | None:
        stmt = select(WithdrawalRequest).where(
            WithdrawalRequest.goal_id == goal_id,
            WithdrawalRequest.status.in_(("PENDING", "APPROVED", "COOLDOWN")),
        )
        return self.db.execute(stmt).scalar_one_or_none()
