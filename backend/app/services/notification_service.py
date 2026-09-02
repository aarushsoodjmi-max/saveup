"""Creates in-app notifications and (best-effort) pushes them.

Deliberately decoupled from the money-moving services: callers invoke
this *after* the ledger/goal/withdrawal transaction has already
committed, and a failure here is logged and swallowed rather than
propagated -- a missed notification should never roll back money that
has already moved.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.services.push_provider import PushProvider, push_provider as default_push_provider

logger = logging.getLogger("saveup.notifications")


class NotificationService:
    def __init__(self, db: Session, push: PushProvider = default_push_provider):
        self.db = db
        self.repo = NotificationRepository(db)
        self.push = push

    def notify(self, *, user_id: UUID, title: str, message: str, type_: str) -> Notification | None:
        try:
            notification = Notification(user_id=user_id, title=title, message=message, type=type_)
            self.repo.create(notification)
            self.db.commit()
            self.push.send(str(user_id), title, message)
            return notification
        except Exception:  # noqa: BLE001 - notifications must never break the caller
            logger.exception("Failed to create/send notification for user %s", user_id)
            self.db.rollback()
            return None

    def notify_deposit(self, *, user_id: UUID, goal_title: str, amount: Decimal) -> None:
        self.notify(
            user_id=user_id,
            title="Deposit successful",
            message=f"You added ₹{amount} to '{goal_title}'. Keep it up!",
            type_="PAYMENT",
        )

    def notify_goal_milestone(self, *, user_id: UUID, goal_title: str, progress_percentage: float) -> None:
        self.notify(
            user_id=user_id,
            title="Milestone reached 🎉",
            message=f"'{goal_title}' is now {progress_percentage:.0f}% funded.",
            type_="GOAL",
        )

    def notify_goal_completed(self, *, user_id: UUID, goal_title: str) -> None:
        self.notify(
            user_id=user_id,
            title="Goal completed! 🎉",
            message=f"You've fully funded '{goal_title}'. Congratulations!",
            type_="GOAL",
        )

    def notify_withdrawal_event(self, *, user_id: UUID, goal_title: str, status: str) -> None:
        messages = {
            "PENDING": f"Your emergency withdrawal request for '{goal_title}' has been submitted.",
            "APPROVED": f"Your withdrawal for '{goal_title}' was approved by your emergency contact.",
            "REJECTED": f"Your withdrawal request for '{goal_title}' was rejected.",
            "COOLDOWN": f"Your withdrawal for '{goal_title}' is now in its cooling-off period.",
            "COMPLETED": f"Your withdrawal for '{goal_title}' has been completed.",
            "CANCELLED": f"Your withdrawal request for '{goal_title}' was cancelled.",
            "FAILED": f"Your withdrawal for '{goal_title}' could not be completed. Please contact support.",
        }
        self.notify(
            user_id=user_id,
            title="Withdrawal update",
            message=messages.get(status, f"Your withdrawal for '{goal_title}' is now {status}."),
            type_="WITHDRAWAL",
        )

    def notify_achievement_unlocked(self, *, user_id: UUID, achievement_title: str) -> None:
        self.notify(
            user_id=user_id,
            title="Achievement unlocked 🏆",
            message=f"You've unlocked '{achievement_title}'.",
            type_="ACHIEVEMENT",
        )
