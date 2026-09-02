from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.time_utils import utc_now
from app.models.goal import Goal
from app.models.user import User
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalCreateRequest, GoalUpdateRequest


class GoalService:
    def __init__(self, db: Session):
        self.db = db
        self.goal_repo = GoalRepository(db)

    def create_goal(self, user: User, payload: GoalCreateRequest) -> Goal:
        goal = Goal(
            user_id=user.id,
            title=payload.title,
            description=payload.description,
            category=payload.category,
            goal_image=payload.goal_image,
            target_amount=payload.target_amount,
            monthly_target=payload.monthly_target,
            deadline=payload.deadline,
            lock_type=payload.lock_type,
            status="ACTIVE",
        )
        self.goal_repo.create(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def get_goal(self, user: User, goal_id: UUID) -> Goal:
        goal = self.goal_repo.get_for_user(goal_id, user.id)
        if goal is None:
            raise NotFoundError("Goal not found")
        return goal

    def list_goals(self, user: User, *, offset: int, limit: int, status: str | None) -> tuple[list[Goal], int]:
        return self.goal_repo.list_for_user(user.id, offset=offset, limit=limit, status=status)

    def update_goal(self, user: User, goal_id: UUID, payload: GoalUpdateRequest) -> Goal:
        goal = self.get_goal(user, goal_id)

        data = payload.model_dump(exclude_unset=True)
        if "target_amount" in data and data["target_amount"] is not None:
            if data["target_amount"] < goal.saved_amount:
                raise ValidationAppError(
                    "target_amount cannot be less than the amount already saved",
                    details={"saved_amount": str(goal.saved_amount)},
                )

        for field, value in data.items():
            setattr(goal, field, value)

        self.db.commit()
        self.db.refresh(goal)
        return goal

    def update_status(self, user: User, goal_id: UUID, new_status: str) -> Goal:
        goal = self.get_goal(user, goal_id)

        if goal.status == "COMPLETED":
            raise ConflictError("A completed goal's status cannot be changed manually")
        if goal.status == "ARCHIVED" and new_status != "ACTIVE":
            raise ConflictError("An archived goal can only be reactivated")

        valid_transitions = {
            "ACTIVE": {"PAUSED", "ARCHIVED"},
            "PAUSED": {"ACTIVE", "ARCHIVED"},
            "ARCHIVED": {"ACTIVE"},
        }
        if new_status not in valid_transitions.get(goal.status, set()):
            raise ConflictError(f"Cannot transition goal from {goal.status} to {new_status}")

        goal.status = new_status
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def delete_goal(self, user: User, goal_id: UUID) -> None:
        goal = self.get_goal(user, goal_id)
        if goal.saved_amount > 0:
            raise ConflictError(
                "Cannot delete a goal with money still saved in it; withdraw or archive it instead"
            )
        self.db.delete(goal)
        self.db.commit()

    @staticmethod
    def mark_completed_if_reached(goal: Goal) -> None:
        """Called by the ledger service inside its own transaction right
        after a successful deposit updates ``saved_amount``.
        """
        if goal.status == "ACTIVE" and goal.saved_amount >= goal.target_amount:
            goal.status = "COMPLETED"
            goal.completed_at = utc_now()
