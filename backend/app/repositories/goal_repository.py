from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.goal import Goal


class GoalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, goal: Goal) -> Goal:
        self.db.add(goal)
        self.db.flush()
        return goal

    def get_by_id(self, goal_id: UUID) -> Goal | None:
        return self.db.get(Goal, goal_id)

    def get_for_user(self, goal_id: UUID, user_id: UUID) -> Goal | None:
        stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_locked(self, goal_id: UUID) -> Goal | None:
        """Row-locks the goal for the duration of the current DB
        transaction (``SELECT ... FOR UPDATE``). Must be called inside
        an active transaction; used exclusively by the ledger service so
        two concurrent deposits/withdrawals against the same goal are
        serialized instead of racing on ``saved_amount``.
        """
        stmt = select(Goal).where(Goal.id == goal_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: UUID,
        *,
        offset: int,
        limit: int,
        status: str | None = None,
    ) -> tuple[list[Goal], int]:
        count_stmt = select(func.count()).select_from(Goal).where(Goal.user_id == user_id)
        list_stmt = select(Goal).where(Goal.user_id == user_id)
        if status:
            count_stmt = count_stmt.where(Goal.status == status)
            list_stmt = list_stmt.where(Goal.status == status)

        total = self.db.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(Goal.created_at.desc()).offset(offset).limit(limit)
        goals = list(self.db.execute(list_stmt).scalars().all())
        return goals, total

    def count_for_user(self, user_id: UUID) -> int:
        return self.db.execute(
            select(func.count()).select_from(Goal).where(Goal.user_id == user_id)
        ).scalar_one()

    def count_all(self) -> int:
        return self.db.execute(select(func.count()).select_from(Goal)).scalar_one()

    def count_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(Goal).where(Goal.status == status)
        return self.db.execute(stmt).scalar_one()

    def sum_saved_amount(self) -> float:
        stmt = select(func.coalesce(func.sum(Goal.saved_amount), 0))
        return self.db.execute(stmt).scalar_one()

    def sum_saved_amount_for_user(self, user_id: UUID):
        stmt = select(func.coalesce(func.sum(Goal.saved_amount), 0)).where(Goal.user_id == user_id)
        return self.db.execute(stmt).scalar_one()

    def count_completed_for_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Goal).where(
            Goal.user_id == user_id, Goal.status == "COMPLETED"
        )
        return self.db.execute(stmt).scalar_one()

    def count_by_status_for_user(self, user_id: UUID, status: str) -> int:
        stmt = select(func.count()).select_from(Goal).where(
            Goal.user_id == user_id, Goal.status == status
        )
        return self.db.execute(stmt).scalar_one()
