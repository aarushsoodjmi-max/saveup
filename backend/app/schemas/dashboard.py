from decimal import Decimal

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_saved: Decimal
    active_goals_count: int
    completed_goals_count: int
    current_streak: int
    best_streak: int
    unread_notifications: int
    unlocked_achievements_count: int
