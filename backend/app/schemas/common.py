from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class APIResponse(BaseModel):
    code: int = 200
    message: str = "OK"
    data: Any = None


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int
    list: list[Any]


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime

