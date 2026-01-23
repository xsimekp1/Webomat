from pydantic import BaseModel, EmailStr
from typing import Literal
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    role: Literal["admin", "sales"]
    is_active: bool
    phone: str | None = None
    notes: str | None = None
    avatar_url: str | None = None
    must_change_password: bool = False
    created_at: datetime | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class UserInDB(User):
    password_hash: str


class UserResponse(BaseModel):
    """User response for API endpoints."""
    id: str
    name: str
    email: str
    role: Literal["admin", "sales"]
    is_active: bool
    phone: str | None = None
    avatar_url: str | None = None
    must_change_password: bool = False


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AdminPasswordReset(BaseModel):
    new_password: str | None = None  # If None, generate random password


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None


class UserListItem(BaseModel):
    """User item for admin listing."""
    id: str
    first_name: str
    last_name: str
    email: str
    role: Literal["admin", "sales"]
    is_active: bool
    created_at: datetime | None = None
