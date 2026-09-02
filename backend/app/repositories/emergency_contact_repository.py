from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.emergency_contact import EmergencyContact


class EmergencyContactRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, contact: EmergencyContact) -> EmergencyContact:
        self.db.add(contact)
        self.db.flush()
        return contact

    def get_for_user(self, contact_id: UUID, user_id: UUID) -> EmergencyContact | None:
        stmt = select(EmergencyContact).where(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: UUID) -> list[EmergencyContact]:
        stmt = select(EmergencyContact).where(EmergencyContact.user_id == user_id).order_by(
            EmergencyContact.created_at.desc()
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, contact: EmergencyContact) -> None:
        self.db.delete(contact)
        self.db.flush()
