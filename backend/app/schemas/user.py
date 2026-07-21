"""User wire formats — note what's absent: hashed_password never leaves storage."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build directly from ORM objects

    id: str
    email: EmailStr
    is_active: bool
    created_at: datetime
