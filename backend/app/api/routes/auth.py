from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserSummary
from app.schemas.common import APIResponse
from app.services.identity import IdentityService


router = APIRouter()


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = IdentityService(db).register(payload)
    return APIResponse(
        data=UserSummary(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            is_admin=user.is_admin,
            permissions=[],
        )
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = IdentityService(db).login(payload)
    return APIResponse(data=TokenResponse(access_token=token))


@router.get("/me")
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    permissions = [permission.code for permission in current_user.permissions(db)]
    return APIResponse(
        data=UserSummary(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            status=current_user.status,
            is_admin=current_user.is_admin,
            permissions=permissions,
        )
    )
