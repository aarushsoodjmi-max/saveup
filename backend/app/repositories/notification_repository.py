from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self, user_id: UUID, *, offset: int, limit: int, unread_only: bool = False
    ) -> tuple[list[Notification], int]:
        count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        list_stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            count_stmt = count_stmt.where(Notification.is_read.is_(False))
            list_stmt = list_stmt.where(Notification.is_read.is_(False))

        total = self.db.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        rows = list(self.db.execute(list_stmt).scalars().all())
        return rows, total

    def count_unread(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        return self.db.execute(stmt).scalar_one()

    def mark_all_read(self, user_id: UUID) -> None:
        stmt = select(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        for notification in self.db.execute(stmt).scalars().all():
            notification.is_read = True
        self.db.flush()
