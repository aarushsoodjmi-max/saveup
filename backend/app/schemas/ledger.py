from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DepositRequest(BaseModel):
    """Direct/manual deposit (e.g. cash reconciliation, admin credit, or
    a payment already confirmed out-of-band). Real card/UPI deposits go
    through ``POST /payments/orders`` + webhook instead.
    """

    goal_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)


class WithdrawalPreviewRequest(BaseModel):
    goal_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)


class AmountRequest(BaseModel):
    """Minimal body for goal-scoped endpoints where the goal id is
    already in the URL path.
    """

    amount: Decimal = Field(gt=0, decimal_places=2)


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    goal_id: UUID
    transaction_type: str
    amount: Decimal
    status: str
    balance_after: Decimal | None
    reference_type: str | None
    reference_id: UUID | None
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime
