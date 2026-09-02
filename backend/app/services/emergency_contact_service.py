from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.emergency_contact import EmergencyContact
from app.models.user import User
from app.repositories.emergency_contact_repository import EmergencyContactRepository
from app.schemas.emergency_contact import EmergencyContactCreateRequest


class EmergencyContactService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmergencyContactRepository(db)

    def create(self, user: User, payload: EmergencyContactCreateRequest) -> EmergencyContact:
        contact = EmergencyContact(
            user_id=user.id,
            contact_name=payload.contact_name,
            relationship_label=payload.relationship_label,
            phone_number=payload.phone_number,
        )
        self.repo.create(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def list_for_user(self, user: User) -> list[EmergencyContact]:
        return self.repo.list_for_user(user.id)

    def delete(self, user: User, contact_id: UUID) -> None:
        contact = self.repo.get_for_user(contact_id, user.id)
        if contact is None:
            raise NotFoundError("Emergency contact not found")

        try:
            self.repo.delete(contact)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(
                "This contact is linked to an active withdrawal request and cannot be deleted"
            ) from None
