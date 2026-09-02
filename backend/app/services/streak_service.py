"""Tracks consecutive deposit-days per user.

Called as a best-effort follow-up after a deposit's own DB transaction
has already committed -- a streak-tracking hiccup should never roll
back money that has already moved.
"""

import logging
from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.time_utils import utc_now
from app.models.streak import Streak
from app.repositories.streak_repository import StreakRepository

logger = logging.getLogger("saveup.streaks")


class StreakService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StreakRepository(db)

    def record_deposit(self, user_id: UUID) -> Streak | None:
        try:
            streak = self.repo.get_or_create(user_id)
            today = utc_now().date()

            if streak.last_saved_date == today:
                pass  # already counted today; no-op
            elif streak.last_saved_date == today - timedelta(days=1):
                streak.current_streak += 1
            else:
                streak.current_streak = 1

            streak.last_saved_date = today
            streak.best_streak = max(streak.best_streak, streak.current_streak)

            self.db.commit()
            self.db.refresh(streak)
            return streak
        except Exception:  # noqa: BLE001
            logger.exception("Failed to update streak for user %s", user_id)
            self.db.rollback()
            return None

    def get_for_user(self, user_id: UUID) -> Streak | None:
        return self.repo.get_for_user(user_id)
