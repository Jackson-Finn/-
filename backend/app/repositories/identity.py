from sqlalchemy.orm import Session

from app.models.entities import Permission, Role, User, UserRole


class IdentityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter_by(email=email).first()

    def create_user(self, *, email: str, password_hash: str, display_name: str) -> User:
        user = User(email=email, password_hash=password_hash, display_name=display_name)
        self.db.add(user)
        self.db.flush()
        return user

    def list_users(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def list_roles(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.id.asc()).all()

    def list_permissions(self) -> list[Permission]:
        return self.db.query(Permission).order_by(Permission.id.asc()).all()

    def assign_roles(self, user_id: int, role_ids: list[int]) -> None:
        self.db.query(UserRole).filter_by(user_id=user_id).delete()
        for role_id in role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=role_id))

