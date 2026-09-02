"""No router-level prefix: ``/achievements`` and ``/streak`` are both
top-level resources per the API spec, not nested under one another.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.achievement import (
    AchievementResponse,
    StreakResponse,
    UnlockedAchievementResponse,
)
from app.services.achievement_service import AchievementService
from app.services.streak_service import StreakService

router = APIRouter(tags=["Achievements & Streaks"])


@router.get("/achievements", response_model=list[AchievementResponse])
def list_achievements(db: Session = Depends(get_db)):
    return AchievementService(db).list_all()


@router.get("/achievements/unlocked", response_model=list[UnlockedAchievementResponse])
def list_unlocked_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = AchievementService(db)
    unlocked = service.list_unlocked_for_user(current_user.id)

    achievements_by_id = {a.id: a for a in service.list_all()}
    return [
        UnlockedAchievementResponse(
            achievement=AchievementResponse.model_validate(achievements_by_id[record.achievement_id]),
            unlocked_at=record.unlocked_at,
        )
        for record in unlocked
        if record.achievement_id in achievements_by_id
    ]


@router.get("/streak", response_model=StreakResponse)
def get_streak(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    streak = StreakService(db).get_for_user(current_user.id)
    if streak is None:
        return StreakResponse(current_streak=0, best_streak=0, last_saved_date=None)
    return streak
