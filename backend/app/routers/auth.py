from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..config import get_settings, Settings
from ..database import get_supabase
from ..dependencies import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from ..schemas.auth import (
    Token,
    User,
    UserResponse,
    PasswordChange,
    UserUpdate,
    LoginRequest,
)

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    OAuth2 compatible token endpoint.

    Login with username (first_name or email) and password.
    Returns JWT access token.
    """
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné přihlašovací údaje",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        settings=settings,
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    JSON login endpoint (alternative to OAuth2 form).

    Login with username (first_name or email) and password.
    Returns JWT access token.
    """
    user = await authenticate_user(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné přihlašovací údaje",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        settings=settings,
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        must_change_password=current_user.must_change_password
    )


@router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update current user's profile."""
    supabase = get_supabase()

    update_dict = {}
    if update_data.first_name is not None:
        update_dict["first_name"] = update_data.first_name
    if update_data.last_name is not None:
        update_dict["last_name"] = update_data.last_name
    if update_data.email is not None:
        update_dict["email"] = update_data.email
    if update_data.phone is not None:
        update_dict["phone"] = update_data.phone

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    result = supabase.table("sellers").update(update_dict).eq(
        "id", current_user.id
    ).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

    updated = result.data[0]
    return UserResponse(
        id=updated["id"],
        name=f"{updated['first_name']} {updated['last_name']}".strip(),
        email=updated["email"],
        role=updated.get("role", "sales"),
        is_active=updated.get("is_active", True),
        phone=updated.get("phone"),
        must_change_password=updated.get("must_change_password", False)
    )


@router.post("/users/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Change current user's password."""
    supabase = get_supabase()

    # Get current password hash
    result = supabase.table("sellers").select("password_hash").eq(
        "id", current_user.id
    ).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    current_hash = result.data[0].get("password_hash", "")

    # Verify current password
    if current_hash.startswith("$2b$") or current_hash.startswith("$2a$"):
        if not verify_password(password_data.current_password, current_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Aktuální heslo není správné"
            )
    else:
        # Legacy plain-text
        if current_hash != password_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Aktuální heslo není správné"
            )

    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nové heslo musí mít alespoň 6 znaků"
        )

    # Hash and save new password
    new_hash = get_password_hash(password_data.new_password)
    supabase.table("sellers").update({
        "password_hash": new_hash,
        "must_change_password": False
    }).eq("id", current_user.id).execute()

    return {"message": "Heslo bylo úspěšně změněno"}
