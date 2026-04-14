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
    is_admin: bool
    permissions: list[str] = []
