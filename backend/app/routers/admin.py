import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_supabase
from ..dependencies import require_admin, get_password_hash
from ..schemas.auth import User, UserListItem, AdminPasswordReset

router = APIRouter(prefix="/admin", tags=["admin"])


def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/users", response_model=list[UserListItem])
async def list_users(
    current_user: Annotated[User, Depends(require_admin)]
):
    """List all users (admin only)."""
    supabase = get_supabase()

    result = supabase.table("sellers").select(
        "id, first_name, last_name, email, role, is_active, created_at"
    ).order("created_at", desc=True).execute()

    return [
        UserListItem(
            id=u["id"],
            first_name=u["first_name"],
            last_name=u["last_name"],
            email=u["email"],
            role=u.get("role", "sales"),
            is_active=u.get("is_active", True),
            created_at=u.get("created_at")
        )
        for u in result.data
    ]


@router.get("/users/{user_id}", response_model=UserListItem)
async def get_user(
    user_id: str,
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get a specific user (admin only)."""
    supabase = get_supabase()

    result = supabase.table("sellers").select(
        "id, first_name, last_name, email, role, is_active, created_at"
    ).eq("id", user_id).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uživatel nenalezen"
        )

    u = result.data[0]
    return UserListItem(
        id=u["id"],
        first_name=u["first_name"],
        last_name=u["last_name"],
        email=u["email"],
        role=u.get("role", "sales"),
        is_active=u.get("is_active", True),
        created_at=u.get("created_at")
    )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    reset_data: AdminPasswordReset,
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Reset a user's password (admin only).

    If new_password is not provided, a random temporary password is generated.
    The user will be required to change their password on next login.
    """
    supabase = get_supabase()

    # Check if user exists
    result = supabase.table("sellers").select("id, first_name, last_name").eq(
        "id", user_id
    ).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uživatel nenalezen"
        )

    user_info = result.data[0]

    # Generate or use provided password
    if reset_data.new_password:
        new_password = reset_data.new_password
    else:
        new_password = generate_temp_password()

    # Hash and save
    password_hash = get_password_hash(new_password)
    supabase.table("sellers").update({
        "password_hash": password_hash,
        "must_change_password": True
    }).eq("id", user_id).execute()

    return {
        "message": f"Heslo pro uživatele {user_info['first_name']} {user_info['last_name']} bylo resetováno",
        "temporary_password": new_password,
        "must_change_password": True
    }


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: Annotated[User, Depends(require_admin)]
):
    """Toggle user's active status (admin only)."""
    supabase = get_supabase()

    # Can't deactivate yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nemůžete deaktivovat svůj vlastní účet"
        )

    # Get current status
    result = supabase.table("sellers").select(
        "id, first_name, last_name, is_active"
    ).eq("id", user_id).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uživatel nenalezen"
        )

    user_info = result.data[0]
    new_status = not user_info.get("is_active", True)

    # Update
    supabase.table("sellers").update({
        "is_active": new_status
    }).eq("id", user_id).execute()

    status_text = "aktivován" if new_status else "deaktivován"
    return {
        "message": f"Uživatel {user_info['first_name']} {user_info['last_name']} byl {status_text}",
        "is_active": new_status
    }
