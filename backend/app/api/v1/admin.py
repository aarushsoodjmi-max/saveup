from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_db, get_pagination, require_admin
from app.models.user import User
from app.schemas.admin import (
    AdminUserResponse,
    AdminWithdrawalRejectRequest,
    DashboardSummaryResponse,
    KYCUpdateRequest,
)
from app.schemas.common import PaginatedResponse, build_pagination_meta
from app.schemas.ledger import TransactionResponse
from app.schemas.withdrawal import WithdrawalResponse
from app.services.admin_service import AdminService
from app.services.withdrawal_service import WithdrawalService

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
def list_users(
    search: str | None = None,
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    users, total = AdminService(db).list_users(offset=pagination.offset, limit=pagination.limit, search=search)
    return PaginatedResponse(
        items=users,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.patch("/users/{user_id}/kyc")
def update_kyc_status(user_id: UUID, payload: KYCUpdateRequest, db: Session = Depends(get_db)):
    user = AdminService(db).update_kyc_status(user_id, payload.kyc_status)
    return {"id": str(user.id), "kyc_status": user.kyc_status}


@router.patch("/users/{user_id}/active")
def set_user_active_status(user_id: UUID, is_active: bool, db: Session = Depends(get_db)):
    user = AdminService(db).set_active_status(user_id, is_active)
    return {"id": str(user.id), "is_active": user.is_active}


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db)):
    return AdminService(db).dashboard_summary()


@router.get("/transactions", response_model=PaginatedResponse[TransactionResponse])
def search_transactions(
    user_id: UUID | None = None,
    goal_id: UUID | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    items, total = AdminService(db).search_transactions(
        offset=pagination.offset,
        limit=pagination.limit,
        user_id=user_id,
        goal_id=goal_id,
        transaction_type=transaction_type,
        status=status,
    )
    return PaginatedResponse(
        items=items,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.get("/withdrawals", response_model=PaginatedResponse[WithdrawalResponse])
def list_pending_withdrawals(db: Session = Depends(get_db), pagination: Pagination = Depends(get_pagination)):
    items, total = AdminService(db).list_pending_withdrawals(offset=pagination.offset, limit=pagination.limit)
    return PaginatedResponse(
        items=items,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.post("/withdrawals/{request_id}/approve", response_model=WithdrawalResponse)
def admin_approve_withdrawal(request_id: UUID, db: Session = Depends(get_db)):
    return WithdrawalService(db).admin_approve_withdrawal(request_id)


@router.post("/withdrawals/{request_id}/reject", response_model=WithdrawalResponse)
def admin_reject_withdrawal(request_id: UUID, payload: AdminWithdrawalRejectRequest, db: Session = Depends(get_db)):
    return WithdrawalService(db).admin_reject_withdrawal(request_id, payload.rejection_reason)
