"""Challenges (group/community savings challenges) are on the product
roadmap (see docs/requirements.md) but out of scope for this MVP pass
-- there is no Challenge model or table yet. These routes exist so the
documented API surface (``GET /challenges``, ``POST /challenges/{id}/join``)
doesn't 404 outright, but they intentionally return an empty/placeholder
result rather than fabricating data.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.common import PaginatedResponse, build_pagination_meta

router = APIRouter(prefix="/challenges", tags=["Challenges"])


@router.get("", response_model=PaginatedResponse[dict])
def list_challenges():
    return PaginatedResponse(items=[], meta=build_pagination_meta(page=1, limit=20, total=0))


@router.post("/{challenge_id}/join")
def join_challenge(challenge_id: UUID, current_user: User = Depends(get_current_user)):
    raise NotFoundError("Challenges are not available in this release")
