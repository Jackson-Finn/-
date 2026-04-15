from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import BaseSchema, TimestampSchema


class AdminNotificationCreateRequest(BaseModel):
    target_scope: str
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    target_user_id: int | None = None
    action_target: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.target_scope == "USER" and not self.target_user_id:
            raise ValueError("target_user_id is required when target_scope is USER")
        if self.target_scope == "ALL":
            self.target_user_id = None
        return self


class AdminNotificationBroadcastResponse(TimestampSchema):
    id: int
    actor_id: int
    target_scope: str
    target_user_id: int | None = None
    title: str
    content: str
    action_target: str | None = None


class UserNotificationResponse(BaseSchema):
    id: int
    event_type: str
    title: str
    content: str
    action_target: str | None = None
    created_at: datetime
    read: bool
