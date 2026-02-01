from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings, Settings
from .database import get_supabase
from .schemas.auth import TokenData, User, UserInDB

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Error verifying password: {e}")
        # Fallback for SHA-256 hashes
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Error hashing password: {e}")
        # Fallback to simple hash for testing
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(
    data: dict,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    if settings is None:
        settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_user_by_username(username: str) -> UserInDB | None:
    """Get user from database by username (first_name) or email."""
    supabase = get_supabase()

    try:
        result = supabase.table("sellers").select("*").or_(
            f"first_name.ilike.{username},email.ilike.{username}"
        ).limit(1).execute()
    except Exception as e:
        print(f"Error fetching user by username: {e}")
        return None

    if not result.data:
        return None

    seller = result.data[0]
    return UserInDB(
        id=seller["id"],
        first_name=seller["first_name"],
        last_name=seller["last_name"],
        email=seller["email"],
        password_hash=seller.get("password_hash", ""),
        role=seller.get("role", "sales"),
        is_active=seller.get("is_active", True),
        phone=seller.get("phone"),
        notes=seller.get("notes"),
        avatar_url=seller.get("avatar_url"),
        must_change_password=seller.get("must_change_password", False),
        created_at=seller.get("created_at")
    )


async def get_user_by_id(user_id: str) -> User | None:
    """Get user from database by ID."""
    supabase = get_supabase()

    try:
        result = supabase.table("sellers").select("*").eq(
            "id", user_id
        ).limit(1).execute()
    except Exception as e:
        print(f"Error fetching user by ID: {e}")
        return None

    if not result.data:
        return None

    seller = result.data[0]
    return User(
        id=seller["id"],
        first_name=seller["first_name"],
        last_name=seller["last_name"],
        email=seller["email"],
        role=seller.get("role", "sales"),
        is_active=seller.get("is_active", True),
        phone=seller.get("phone"),
        notes=seller.get("notes"),
        avatar_url=seller.get("avatar_url"),
        must_change_password=seller.get("must_change_password", False),
        onboarded_at=seller.get("onboarded_at"),
        bank_account=seller.get("bank_account"),
        bank_account_iban=seller.get("bank_account_iban"),
        created_at=seller.get("created_at")
    )


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate a user with username and password."""
    user = await get_user_by_username(username)

    if not user:
        return None

    if not user.is_active:
        return None

    # Check if password is already hashed (bcrypt hashes start with $2b$)
    if user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$"):
        if not verify_password(password, user.password_hash):
            return None
    else:
        # Legacy plain-text password comparison (for migration period)
        if user.password_hash != password:
            return None

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Verify the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role(["admin"])
require_sales_or_admin = require_role(["admin", "sales"])
