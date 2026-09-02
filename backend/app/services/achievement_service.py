"""Automatic achievement-unlock evaluation.

Re-evaluates every achievement a user hasn't already unlocked against
their current metrics (total saved, current streak, goals completed)
and unlocks any that now qualify. Designed to be called as a
best-effort follow-up after a deposit -- like notifications and
streaks, a failure here is logged and swallowed rather than
propagated.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.achievement import Achievement
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.streak_repository import StreakRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger("saveup.achievements")


class AchievementService:
    def __init__(self, db: Session, notification_service: NotificationService | None = None):
        self.db = db
        self.repo = AchievementRepository(db)
        self.goal_repo = GoalRepository(db)
        self.streak_repo = StreakRepository(db)
        self.notification_service = notification_service or NotificationService(db)

    def evaluate_and_unlock_for_user(self, user_id: UUID) -> list[Achievement]:
        try:
            total_saved = Decimal(str(self.goal_repo.sum_saved_amount_for_user(user_id)))
            goals_completed = self.goal_repo.count_completed_for_user(user_id)
            streak = self.streak_repo.get_for_user(user_id)
            streak_days = streak.current_streak if streak else 0

            metric_values: dict[str, Decimal] = {
                "TOTAL_SAVED": total_saved,
                "STREAK_DAYS": Decimal(streak_days),
                "GOALS_COMPLETED": Decimal(goals_completed),
            }

            newly_unlocked: list[Achievement] = []
            for achievement in self.repo.list_all():
                if self.repo.is_unlocked(user_id, achievement.id):
                    continue
                current_value = metric_values.get(achievement.metric)
                if current_value is not None and current_value >= achievement.required_value:
                    self.repo.unlock(user_id, achievement.id)
                    newly_unlocked.append(achievement)

            if newly_unlocked:
                self.db.commit()
                for achievement in newly_unlocked:
                    self.notification_service.notify_achievement_unlocked(
                        user_id=user_id, achievement_title=achievement.title
                    )
            return newly_unlocked
        except Exception:  # noqa: BLE001
            logger.exception("Failed to evaluate achievements for user %s", user_id)
            self.db.rollback()
            return []

    def list_all(self) -> list[Achievement]:
        return self.repo.list_all()

    def list_unlocked_for_user(self, user_id: UUID):
        return self.repo.list_unlocked_for_user(user_id)
