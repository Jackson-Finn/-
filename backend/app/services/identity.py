from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.identity import IdentityRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class IdentityService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IdentityRepository(db)

    def register(self, payload: RegisterRequest):
        if self.repo.get_user_by_email(payload.email):
            raise AppError("Email already registered", status_code=409)
        user = self.repo.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> str:
        user = self.repo.get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AppError("Invalid credentials", status_code=401)
        return create_access_token(str(user.id))

    def list_users(self):
        return self.repo.list_users()

    def list_roles(self):
        return self.repo.list_roles()

    def list_permissions(self):
        return self.repo.list_permissions()

    def assign_roles(self, user_id: int, role_ids: list[int]) -> None:
        self.repo.assign_roles(user_id, role_ids)
        self.db.commit()
