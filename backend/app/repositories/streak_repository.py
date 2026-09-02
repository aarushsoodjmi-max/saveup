from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.streak import Streak


class StreakRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: UUID) -> Streak | None:
        stmt = select(Streak).where(Streak.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_for_user_locked(self, user_id: UUID) -> Streak | None:
        stmt = select(Streak).where(Streak.user_id == user_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create(self, user_id: UUID) -> Streak:
        streak = self.get_for_user_locked(user_id)
        if streak is None:
            streak = Streak(user_id=user_id, current_streak=0, best_streak=0)
            self.db.add(streak)
            self.db.flush()
        return streak
