from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_current_user, get_db, get_pagination
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.common import MessageResponse, PaginatedResponse, build_pagination_meta
from app.schemas.notification import NotificationResponse, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    repo = NotificationRepository(db)
    items, total = repo.list_for_user(
        current_user.id, offset=pagination.offset, limit=pagination.limit, unread_only=unread_only
    )
    return PaginatedResponse(
        items=items,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    return UnreadCountResponse(unread_count=repo.count_unread(current_user.id))


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    repo = NotificationRepository(db)
    notification = repo.get_for_user(notification_id, current_user.id)
    if notification is None:
        raise NotFoundError("Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all", response_model=MessageResponse)
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = NotificationRepository(db)
    repo.mark_all_read(current_user.id)
    return MessageResponse(message="All notifications marked as read")
