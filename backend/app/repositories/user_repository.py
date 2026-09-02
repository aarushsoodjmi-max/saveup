from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_phone(self, phone_number: str) -> User | None:
        stmt = select(User).where(User.phone_number == phone_number)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, *, phone_number: str, name: str) -> User:
        user = User(phone_number=phone_number, name=name)
        self.db.add(user)
        self.db.flush()
        return user

    def list_all(self, *, offset: int, limit: int, search: str | None = None) -> tuple[list[User], int]:
        filters = []
        if search:
            like = f"%{search}%"
            filters.append((User.name.ilike(like)) | (User.phone_number.ilike(like)))

        count_stmt = select(func.count()).select_from(User)
        list_stmt = select(User)
        for f in filters:
            count_stmt = count_stmt.where(f)
            list_stmt = list_stmt.where(f)

        total = self.db.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        users = list(self.db.execute(list_stmt).scalars().all())
        return users, total

    def count_active(self) -> int:
        stmt = select(func.count()).select_from(User).where(User.is_active.is_(True))
        return self.db.execute(stmt).scalar_one()

    def count_pending_kyc(self) -> int:
        stmt = select(func.count()).select_from(User).where(User.kyc_status == "PENDING")
        return self.db.execute(stmt).scalar_one()

    def count_total(self) -> int:
        return self.db.execute(select(func.count()).select_from(User)).scalar_one()
