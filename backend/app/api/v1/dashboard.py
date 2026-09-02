from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.streak_repository import StreakRepository
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal_repo = GoalRepository(db)
    streak = StreakRepository(db).get_for_user(current_user.id)

    return DashboardResponse(
        total_saved=Decimal(str(goal_repo.sum_saved_amount_for_user(current_user.id))),
        active_goals_count=goal_repo.count_by_status_for_user(current_user.id, "ACTIVE"),
        completed_goals_count=goal_repo.count_completed_for_user(current_user.id),
        current_streak=streak.current_streak if streak else 0,
        best_streak=streak.best_streak if streak else 0,
        unread_notifications=NotificationRepository(db).count_unread(current_user.id),
        unlocked_achievements_count=len(
            AchievementRepository(db).list_unlocked_for_user(current_user.id)
        ),
    )
