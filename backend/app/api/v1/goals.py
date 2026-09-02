from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_current_user, get_db, get_idempotency_key, get_pagination
from app.core.exceptions import ConflictError
from app.models.user import User
from app.schemas.common import PaginatedResponse, build_pagination_meta
from app.schemas.goal import GoalCreateRequest, GoalResponse, GoalStatusUpdateRequest, GoalUpdateRequest
from app.schemas.ledger import AmountRequest, TransactionResponse
from app.services.goal_service import GoalService
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal(payload: GoalCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return GoalService(db).create_goal(current_user, payload)


@router.get("", response_model=PaginatedResponse[GoalResponse])
def list_goals(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    goals, total = GoalService(db).list_goals(
        current_user, offset=pagination.offset, limit=pagination.limit, status=status
    )
    return PaginatedResponse(
        items=goals,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return GoalService(db).get_goal(current_user, goal_id)


@router.api_route("/{goal_id}", methods=["PUT", "PATCH"], response_model=GoalResponse)
def update_goal(
    goal_id: UUID,
    payload: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GoalService(db).update_goal(current_user, goal_id, payload)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    GoalService(db).delete_goal(current_user, goal_id)
    return None


@router.patch("/{goal_id}/pause", response_model=GoalResponse)
def pause_goal(goal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return GoalService(db).update_status(current_user, goal_id, "PAUSED")


@router.patch("/{goal_id}/resume", response_model=GoalResponse)
def resume_goal(goal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return GoalService(db).update_status(current_user, goal_id, "ACTIVE")


@router.patch("/{goal_id}/archive", response_model=GoalResponse)
def archive_goal(goal_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return GoalService(db).update_status(current_user, goal_id, "ARCHIVED")


@router.patch("/{goal_id}/status", response_model=GoalResponse)
def set_goal_status(
    goal_id: UUID,
    payload: GoalStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GoalService(db).update_status(current_user, goal_id, payload.status)


@router.post("/{goal_id}/withdraw", response_model=TransactionResponse)
def withdraw_from_easy_goal(
    goal_id: UUID,
    payload: AmountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    """Direct, immediate withdrawal -- only permitted for EASY lock
    goals, which carry no lock guarantee and therefore don't need the
    emergency-contact/OTP/cooldown workflow (see ``/withdrawals`` for
    MEDIUM/HARD lock goals).
    """
    goal_service = GoalService(db)
    goal = goal_service.get_goal(current_user, goal_id)

    if goal.lock_type != "EASY":
        raise ConflictError(
            "This goal is locked; use the emergency withdrawal workflow (POST /withdrawals) instead"
        )

    return LedgerService(db).withdraw(
        user=current_user,
        goal_id=goal_id,
        amount=payload.amount,
        reference_type="direct_withdrawal",
        idempotency_key=idempotency_key,
    )
