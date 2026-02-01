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
    onboarded_at: datetime | None = None
    bank_account: str | None = None
    bank_account_iban: str | None = None
    created_at: datetime | None = None
    preferred_language: str = "cs"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def needs_onboarding(self) -> bool:
        """Check if user needs to complete onboarding."""
        return self.onboarded_at is None


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
    onboarded_at: datetime | None = None
    bank_account: str | None = None
    bank_account_iban: str | None = None
    needs_onboarding: bool = False
    preferred_language: str = "cs"


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
    bank_account: str | None = None
    bank_account_iban: str | None = None
    preferred_language: str | None = None


class OnboardingComplete(BaseModel):
    """Data required to complete onboarding."""
    first_name: str
    last_name: str
    email: str
    phone: str
    bank_account: str | None = None  # Either bank_account or bank_account_iban required
    bank_account_iban: str | None = None


class LanguageUpdate(BaseModel):
    """Language update model."""
    preferred_language: Literal["cs", "en"]


class UserListItem(BaseModel):
    """User item for admin listing."""
    id: str
    first_name: str
    last_name: str
    email: str
    role: Literal["admin", "sales"]
    is_active: bool
    created_at: datetime | None = None
    preferred_language: str = "cs"
