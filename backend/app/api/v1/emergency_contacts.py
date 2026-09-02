from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.emergency_contact import EmergencyContactCreateRequest, EmergencyContactResponse
from app.services.emergency_contact_service import EmergencyContactService

router = APIRouter(prefix="/emergency-contacts", tags=["Emergency Contacts"])


@router.post("", response_model=EmergencyContactResponse, status_code=201)
def create_emergency_contact(
    payload: EmergencyContactCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return EmergencyContactService(db).create(current_user, payload)


@router.get("", response_model=list[EmergencyContactResponse])
def list_emergency_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return EmergencyContactService(db).list_for_user(current_user)


@router.delete("/{contact_id}", status_code=204)
def delete_emergency_contact(
    contact_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    EmergencyContactService(db).delete(current_user, contact_id)
    return None
