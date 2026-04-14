from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.entities import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("Authentication required", status_code=401)
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise AppError("User not found", status_code=401)
    return user


def get_optional_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    return db.get(User, int(payload["sub"]))


def require_permissions(*permission_codes: str):
    def checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        granted = {permission.code for permission in current_user.permissions(db)}
        if not set(permission_codes).issubset(granted):
            raise AppError("Permission denied", status_code=403)
        return current_user

    return checker
