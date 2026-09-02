from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement, UserAchievement


class AchievementRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Achievement]:
        return list(self.db.execute(select(Achievement)).scalars().all())

    def get_by_code(self, code: str) -> Achievement | None:
        stmt = select(Achievement).where(Achievement.code == code)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_unlocked_for_user(self, user_id: UUID) -> list[UserAchievement]:
        stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def is_unlocked(self, user_id: UUID, achievement_id: UUID) -> bool:
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def unlock(self, user_id: UUID, achievement_id: UUID) -> UserAchievement:
        record = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        self.db.add(record)
        self.db.flush()
        return record
