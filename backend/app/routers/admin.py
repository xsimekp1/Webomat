import secrets
import string
from datetime import datetime, timedelta
from typing import Annotated
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_supabase
from ..dependencies import require_admin, get_password_hash
from ..schemas.auth import User, UserListItem, AdminPasswordReset

router = APIRouter(prefix="/admin", tags=["admin"])


class WeeklyInvoice(BaseModel):
    """Týdenní souhrn fakturace."""
    week_start: str  # ISO date
    week_end: str
    total_amount: float
    invoice_count: int


class AdminDashboardStats(BaseModel):
    """Statistiky pro admin dashboard."""
    projects_in_production: int
    projects_delivered: int
    projects_won: int
    total_active_projects: int
    weekly_invoices: list[WeeklyInvoice]  # 12 týdnů (3 měsíce)


@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_admin_dashboard_stats(
    current_user: Annotated[User, Depends(require_admin)]
):
    """
    Statistiky pro admin dashboard.

    Vrací:
    - Počet rozpracovaných projektů (won, in_production, delivered)
    - Týdenní fakturace za poslední 3 měsíce
    """
    supabase = get_supabase()

    # Počty projektů podle statusu
    projects_result = supabase.table("website_projects").select("status").execute()

    projects_won = 0
    projects_in_production = 0
    projects_delivered = 0

    for p in projects_result.data or []:
        status = p.get("status")
        if status == "won":
            projects_won += 1
        elif status == "in_production":
            projects_in_production += 1
        elif status == "delivered":
            projects_delivered += 1

    total_active = projects_won + projects_in_production + projects_delivered

    # Týdenní fakturace za poslední 12 týdnů (3 měsíce)
    weekly_invoices = []
    today = datetime.utcnow().date()

    # Začátek aktuálního týdne (pondělí)
    current_week_start = today - timedelta(days=today.weekday())

    for i in range(12):  # 12 týdnů zpětně
        week_start = current_week_start - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)

        # Dotaz na faktury v tomto týdnu
        invoices_result = (
            supabase.table("invoices_issued")
            .select("amount_total")
            .gte("issue_date", week_start.isoformat())
            .lte("issue_date", week_end.isoformat())
            .in_("status", ["issued", "paid"])
            .execute()
        )

        total_amount = sum(
            inv.get("amount_total", 0) or 0
            for inv in (invoices_result.data or [])
        )
        invoice_count = len(invoices_result.data or [])

        weekly_invoices.append(WeeklyInvoice(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            total_amount=total_amount,
            invoice_count=invoice_count,
        ))

    # Obrátit pořadí - od nejstaršího po nejnovější
    weekly_invoices.reverse()

    return AdminDashboardStats(
        projects_in_production=projects_in_production,
        projects_delivered=projects_delivered,
        projects_won=projects_won,
        total_active_projects=total_active,
        weekly_invoices=weekly_invoices,
    )


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

    # If deactivating, check for unpaid balance
    if not new_status:
        # Calculate balance from ledger
        earned_result = (
            supabase.table("ledger_entries")
            .select("amount")
            .eq("seller_id", user_id)
            .eq("entry_type", "commission_earned")
            .execute()
        )
        total_earned = sum(r["amount"] for r in earned_result.data) if earned_result.data else 0

        payout_result = (
            supabase.table("ledger_entries")
            .select("amount")
            .eq("seller_id", user_id)
            .in_("entry_type", ["payout_reserved", "payout_paid"])
            .execute()
        )
        total_payouts = sum(r["amount"] for r in payout_result.data) if payout_result.data else 0

        balance = total_earned - total_payouts

        if balance > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nelze deaktivovat obchodníka s nevyplaceným zůstatkem {balance:.0f} Kč. Nejprve vyplaťte provize."
            )

    # Update
    supabase.table("sellers").update({
        "is_active": new_status
    }).eq("id", user_id).execute()

    status_text = "aktivován" if new_status else "deaktivován"
    return {
        "message": f"Uživatel {user_info['first_name']} {user_info['last_name']} byl {status_text}",
        "is_active": new_status
    }
