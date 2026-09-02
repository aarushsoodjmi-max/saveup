from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.goal_repository import GoalRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.withdrawal_repository import WithdrawalRepository
from app.schemas.admin import AdminUserResponse, DashboardSummaryResponse


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.goal_repo = GoalRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.withdrawal_repo = WithdrawalRepository(db)

    def list_users(
        self, *, offset: int, limit: int, search: str | None = None
    ) -> tuple[list[AdminUserResponse], int]:
        users, total = self.user_repo.list_all(offset=offset, limit=limit, search=search)
        results = [
            AdminUserResponse(
                id=user.id,
                phone_number=user.phone_number,
                name=user.name,
                email=user.email,
                kyc_status=user.kyc_status,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                total_saved=Decimal(str(self.goal_repo.sum_saved_amount_for_user(user.id))),
            )
            for user in users
        ]
        return results, total

    def update_kyc_status(self, user_id: UUID, kyc_status: str) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        user.kyc_status = kyc_status
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_active_status(self, user_id: UUID, is_active: bool) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def dashboard_summary(self) -> DashboardSummaryResponse:
        total_saved = Decimal(str(self.goal_repo.sum_saved_amount()))
        total_withdrawn = Decimal(str(self.transaction_repo.sum_by_type("WITHDRAWAL")))

        return DashboardSummaryResponse(
            total_users=self.user_repo.count_total(),
            active_users=self.user_repo.count_active(),
            total_goals=self.goal_repo.count_all(),
            active_goals=self.goal_repo.count_by_status("ACTIVE"),
            completed_goals=self.goal_repo.count_by_status("COMPLETED"),
            total_saved_amount=total_saved,
            total_withdrawn_amount=total_withdrawn,
            pending_kyc_count=self.user_repo.count_pending_kyc(),
            pending_withdrawal_count=self.withdrawal_repo.count_pending(),
        )

    def search_transactions(
        self,
        *,
        offset: int,
        limit: int,
        user_id: UUID | None = None,
        goal_id: UUID | None = None,
        transaction_type: str | None = None,
        status: str | None = None,
    ):
        return self.transaction_repo.search(
            offset=offset,
            limit=limit,
            user_id=user_id,
            goal_id=goal_id,
            transaction_type=transaction_type,
            status=status,
        )

    def list_pending_withdrawals(self, *, offset: int, limit: int):
        return self.withdrawal_repo.list_pending(offset=offset, limit=limit)
