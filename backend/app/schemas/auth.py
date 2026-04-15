from pydantic import BaseModel, EmailStr

from app.schemas.common import BaseSchema


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSummary(BaseSchema):
    id: int
    email: str
    display_name: str
    status: str
    presence_status: str
    is_admin: bool
    permissions: list[str] = []


class WorkspaceSummary(BaseSchema):
    unread_messages: int = 0
    unread_notifications: int = 0
    favorites: int = 0
    recent_history: int = 0
    active_orders: int = 0
