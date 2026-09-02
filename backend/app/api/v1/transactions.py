from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import Pagination, get_current_user, get_db, get_pagination
from app.models.user import User
from app.schemas.common import PaginatedResponse, build_pagination_meta
from app.schemas.ledger import TransactionResponse
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=PaginatedResponse[TransactionResponse])
def list_transactions(
    goal_id: UUID | None = None,
    transaction_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    ledger_service = LedgerService(db)
    transactions, total = ledger_service.list_for_user(
        current_user,
        offset=pagination.offset,
        limit=pagination.limit,
        goal_id=goal_id,
        transaction_type=transaction_type,
    )
    return PaginatedResponse(
        items=transactions,
        meta=build_pagination_meta(page=pagination.page, limit=pagination.limit, total=total),
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return LedgerService(db).get_transaction_for_user(transaction_id, current_user)
