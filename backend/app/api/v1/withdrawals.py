from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_current_user, get_db, get_pagination
from app.models.user import User
from app.schemas.common import PaginatedResponse, build_pagination_meta
from app.schemas.withdrawal import (
    WithdrawalApproveRequest,
    WithdrawalRejectRequest,
    WithdrawalRequestCreate,
    WithdrawalResponse,
)
from app.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/withdrawals", tags=["Emergency Withdrawals"])


def _with_debug_otp(request, debug_otp: str | None) -> WithdrawalResponse:
    response = WithdrawalResponse.model_validate(request)
    response.debug_otp = debug_otp
    return response


@router.post("", response_model=WithdrawalResponse, status_code=201)
def request_withdrawal(
    payload: WithdrawalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request, debug_otp = WithdrawalService(db).request_withdrawal(current_user, payload)
    return _with_debug_otp(request, debug_otp)


@router.get("", response_model=PaginatedResponse[WithdrawalResponse])
def list_withdrawals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    items, total = WithdrawalService(db).list_for_user(
        current_user, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=items,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.get("/{request_id}", response_model=WithdrawalResponse)
def get_withdrawal(request_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return WithdrawalService(db).get_for_user(current_user, request_id)


@router.post("/{request_id}/resend-otp")
def resend_otp(request_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    debug_otp = WithdrawalService(db).resend_otp(current_user, request_id)
    return {"message": "Verification code resent to the emergency contact", "debug_otp": debug_otp}


@router.post("/{request_id}/approve", response_model=WithdrawalResponse)
def approve_withdrawal(request_id: UUID, payload: WithdrawalApproveRequest, db: Session = Depends(get_db)):
    """Called by the emergency contact, who has no SaveUp account of
    their own -- intentionally not behind ``get_current_user``. The
    request's UUID (unguessable) plus the one-time OTP sent to the
    contact's phone are the credential.
    """
    return WithdrawalService(db).approve_withdrawal(request_id, payload.otp)


@router.post("/{request_id}/reject", response_model=WithdrawalResponse)
def reject_withdrawal(request_id: UUID, payload: WithdrawalRejectRequest, db: Session = Depends(get_db)):
    """Called by the emergency contact -- same auth model as ``/approve``."""
    return WithdrawalService(db).reject_withdrawal(request_id, payload.otp, payload.rejection_reason)


@router.post("/{request_id}/cancel", response_model=WithdrawalResponse)
def cancel_withdrawal(request_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return WithdrawalService(db).cancel_withdrawal(current_user, request_id)


@router.post("/{request_id}/complete", response_model=WithdrawalResponse)
def complete_withdrawal(request_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Releases the funds once the lock-type cooldown has elapsed. In a
    production deployment this would typically also be invoked by a
    scheduled job as soon as ``cooldown_ends_at`` passes; exposing it
    here lets the owning user (or a cron hitting this same endpoint)
    trigger it without requiring a background worker in this MVP.
    """
    return WithdrawalService(db).complete_withdrawal(current_user, request_id)
