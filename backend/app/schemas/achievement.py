from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    description: str | None
    badge_image: str | None
    metric: str
    required_value: Decimal


class UnlockedAchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    achievement: AchievementResponse
    unlocked_at: datetime


class StreakResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_streak: int
    best_streak: int
    last_saved_date: date | None = None
