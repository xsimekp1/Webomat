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
    OnboardingComplete,
    LanguageUpdate,
)
from datetime import datetime
from ..audit import log_login, log_login_failed, log_entity_change

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    OAuth2 compatible token endpoint.

    Login with username (first_name or email) and password.
    Returns JWT access token.
    """
    try:
        user = await authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při přihlášení: {str(e)}",
        )

    if not user:
        log_login_failed(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné přihlašovací údaje",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        settings=settings,
        expires_delta=access_token_expires,
    )

    log_login(user.id, user.email)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login_json(
    login_data: LoginRequest, settings: Annotated[Settings, Depends(get_settings)]
):
    """
    JSON login endpoint (alternative to OAuth2 form).

    Login with username (first_name or email) and password.
    Returns JWT access token.
    """
    user = await authenticate_user(login_data.username, login_data.password)

    if not user:
        log_login_failed(login_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné přihlašovací údaje",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        settings=settings,
        expires_delta=access_token_expires,
    )

    log_login(user.id, user.email)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        name=current_user.full_name,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        must_change_password=current_user.must_change_password,
        onboarded_at=current_user.onboarded_at,
        bank_account=current_user.bank_account,
        bank_account_iban=current_user.bank_account_iban,
        needs_onboarding=current_user.needs_onboarding,
        preferred_language=getattr(current_user, "preferred_language", "cs"),
    )


@router.post("/users/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
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
    if update_data.bank_account is not None:
        update_dict["bank_account"] = update_data.bank_account
    if update_data.bank_account_iban is not None:
        update_dict["bank_account_iban"] = update_data.bank_account_iban
    if update_data.preferred_language is not None:
        update_dict["preferred_language"] = update_data.preferred_language

    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    result = (
        supabase.table("sellers")
        .update(update_dict)
        .eq("id", current_user.id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )

    if result.data:
        updated = result.data[0]
        return UserResponse(
            id=updated.get("id", current_user.id),
            name=f"{updated.get('first_name', '')} {updated.get('last_name', '')}".strip(),
            email=updated.get("email", current_user.email),
            role=updated.get("role", "sales"),
            is_active=updated.get("is_active", True),
            phone=updated.get("phone"),
            avatar_url=updated.get("avatar_url"),
            must_change_password=updated.get("must_change_password", False),
            onboarded_at=updated.get("onboarded_at"),
            bank_account=updated.get("bank_account"),
            bank_account_iban=updated.get("bank_account_iban"),
            needs_onboarding=updated.get("onboarded_at") is None,
            preferred_language=updated.get("preferred_language", "cs"),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.post("/users/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Change current user's password."""
    supabase = get_supabase()

    # Get current password hash
    result = (
        supabase.table("sellers")
        .select("password_hash")
        .eq("id", current_user.id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    current_hash = result.data[0].get("password_hash", "")

    # Verify current password
    if current_hash.startswith("$2b$") or current_hash.startswith("$2a$"):
        if not verify_password(password_data.current_password, current_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Aktuální heslo není správné",
            )
    else:
        # Legacy plain-text
        if current_hash != password_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Aktuální heslo není správné",
            )

    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nové heslo musí mít alespoň 6 znaků",
        )

    # Hash and save new password
    new_hash = get_password_hash(password_data.new_password)
    supabase.table("sellers").update(
        {"password_hash": new_hash, "must_change_password": False}
    ).eq("id", current_user.id).execute()

    return {"message": "Heslo bylo úspěšně změněno"}


@router.post("/users/me/onboarding", response_model=UserResponse)
async def complete_onboarding(
    data: OnboardingComplete,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Complete user onboarding.

    Required fields: first_name, last_name, email, phone
    At least one of bank_account or bank_account_iban must be provided.
    """
    # Validate bank account
    if not data.bank_account and not data.bank_account_iban:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Musíte vyplnit číslo účtu nebo IBAN pro výplatu provizí",
        )

    supabase = get_supabase()

    update_dict = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "onboarded_at": datetime.utcnow().isoformat(),
    }

    if data.bank_account:
        update_dict["bank_account"] = data.bank_account
    if data.bank_account_iban:
        update_dict["bank_account_iban"] = data.bank_account_iban

    result = (
        supabase.table("sellers")
        .update(update_dict)
        .eq("id", current_user.id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se dokončit onboarding",
        )

    updated = result.data[0]
    return UserResponse(
        id=updated["id"],
        name=f"{updated['first_name']} {updated['last_name']}".strip(),
        email=updated["email"],
        role=updated.get("role", "sales"),
        is_active=updated.get("is_active", True),
        phone=updated.get("phone"),
        avatar_url=updated.get("avatar_url"),
        must_change_password=updated.get("must_change_password", False),
        onboarded_at=updated.get("onboarded_at"),
        bank_account=updated.get("bank_account"),
        bank_account_iban=updated.get("bank_account_iban"),
        needs_onboarding=False,
)


@router.put("/users/me")
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update user profile information."""
    supabase = get_supabase()
    
    # Build update dict with only provided fields
    update_data = {}
    if user_update.first_name is not None:
        update_data["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_data["last_name"] = user_update.last_name
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.phone is not None:
        update_data["phone"] = user_update.phone
    if user_update.bank_account is not None:
        update_data["bank_account"] = user_update.bank_account
    if user_update.bank_account_iban is not None:
        update_data["bank_account_iban"] = user_update.bank_account_iban
    if user_update.preferred_language is not None:
        update_data["preferred_language"] = user_update.preferred_language
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    
    # Add updated timestamp
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Update user in sellers table
    result = (
        supabase.table("sellers")
        .update(update_data)
        .eq("id", current_user.id)
        .execute()
    )
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        )
    
    # Log the change
    log_entity_change(
        user_id=current_user.id,
        user_email=current_user.email,
        action="profile_updated",
        entity_type="user",
        entity_id=current_user.id,
        old_values={},
        new_values=update_data,
    )
    
    return {"message": "Profile updated successfully"}


@router.put("/users/me/language")
async def update_user_language(
    language_data: LanguageUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update user's preferred language."""
    supabase = get_supabase()

    # Update preferred_language in sellers table
    result = (
        supabase.table("sellers")
        .update({"preferred_language": language_data.preferred_language})
        .eq("id", current_user.id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language",
        )

    return {"message": "Language updated successfully"}
