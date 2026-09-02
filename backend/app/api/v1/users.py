from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UpdateProfileRequest, UserProfile
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.api_route("/me", methods=["PUT", "PATCH"], response_model=UserProfile)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = UserService(db)
    return service.update_profile(current_user, payload)
