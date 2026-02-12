import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str | None = None
    license_number: str | None = None


class UserLogin(BaseModel):
    phone: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str | None = None
    phone: str
    full_name: str
    license_number: str | None = None
    avatar_url: str | None = None
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    login_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdateStatus(BaseModel):
    is_active: bool
    reason: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
