"""
Platform Feedback Router

Endpoints for submitting and managing internal platform feedback.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_supabase
from ..dependencies import require_sales_or_admin, require_admin
from ..schemas.auth import User
from ..schemas.crm import (
    PlatformFeedbackCreate,
    PlatformFeedbackUpdate,
    PlatformFeedbackResponse,
)

router = APIRouter(tags=["Feedback"])


def get_seller_name(supabase, seller_id: str | None) -> str | None:
    """Get seller name by ID."""
    if not seller_id:
        return None
    result = (
        supabase.table("sellers")
        .select("first_name, last_name")
        .eq("id", seller_id)
        .limit(1)
        .execute()
    )
    if result.data:
        s = result.data[0]
        return f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or None
    return None


# ============================================
# User Feedback Endpoints
# ============================================


@router.post(
    "/feedback",
    response_model=PlatformFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    data: PlatformFeedbackCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Submit feedback about the platform."""
    supabase = get_supabase()

    # Validate content
    if not data.content or len(data.content.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zpětná vazba musí mít alespoň 10 znaků",
        )

    if len(data.content) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zpětná vazba je příliš dlouhá (max 10000 znaků)",
        )

    result = supabase.table("platform_feedback").insert({
        "submitted_by": current_user.id,
        "content": data.content.strip(),
        "category": data.category.value if hasattr(data.category, "value") else data.category,
        "priority": data.priority.value if hasattr(data.priority, "value") else data.priority,
        "page_url": data.page_url,
        "status": "open",
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se odeslat zpětnou vazbu",
        )

    row = result.data[0]
    return PlatformFeedbackResponse(
        id=row["id"],
        submitted_by=row["submitted_by"],
        submitter_name=f"{current_user.first_name} {current_user.last_name}".strip(),
        content=row["content"],
        category=row["category"],
        priority=row["priority"],
        status=row["status"],
        admin_note=row.get("admin_note"),
        handled_by=row.get("handled_by"),
        handler_name=None,
        handled_at=row.get("handled_at"),
        page_url=row.get("page_url"),
        created_at=row.get("created_at"),
    )


@router.get("/feedback", response_model=list[PlatformFeedbackResponse])
async def list_my_feedback(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """List feedback submitted by current user."""
    supabase = get_supabase()

    result = (
        supabase.table("platform_feedback")
        .select("*")
        .eq("submitted_by", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )

    feedbacks = []
    for row in result.data or []:
        feedbacks.append(
            PlatformFeedbackResponse(
                id=row["id"],
                submitted_by=row["submitted_by"],
                submitter_name=f"{current_user.first_name} {current_user.last_name}".strip(),
                content=row["content"],
                category=row["category"],
                priority=row["priority"],
                status=row["status"],
                admin_note=row.get("admin_note"),
                handled_by=row.get("handled_by"),
                handler_name=get_seller_name(supabase, row.get("handled_by")),
                handled_at=row.get("handled_at"),
                page_url=row.get("page_url"),
                created_at=row.get("created_at"),
            )
        )

    return feedbacks


# ============================================
# Admin Feedback Endpoints
# ============================================


@router.get("/admin/feedback", response_model=list[PlatformFeedbackResponse])
async def list_all_feedback(
    current_user: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all platform feedback (admin only)."""
    supabase = get_supabase()

    query = (
        supabase.table("platform_feedback")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )

    if status_filter:
        query = query.eq("status", status_filter)
    if category:
        query = query.eq("category", category)

    result = query.execute()

    # Batch fetch submitter names
    submitter_ids = list(set(row["submitted_by"] for row in result.data or []))
    submitter_names = {}
    if submitter_ids:
        sellers_result = (
            supabase.table("sellers")
            .select("id, first_name, last_name")
            .in_("id", submitter_ids)
            .execute()
        )
        for s in sellers_result.data or []:
            submitter_names[s["id"]] = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()

    feedbacks = []
    for row in result.data or []:
        feedbacks.append(
            PlatformFeedbackResponse(
                id=row["id"],
                submitted_by=row["submitted_by"],
                submitter_name=submitter_names.get(row["submitted_by"]),
                content=row["content"],
                category=row["category"],
                priority=row["priority"],
                status=row["status"],
                admin_note=row.get("admin_note"),
                handled_by=row.get("handled_by"),
                handler_name=get_seller_name(supabase, row.get("handled_by")),
                handled_at=row.get("handled_at"),
                page_url=row.get("page_url"),
                created_at=row.get("created_at"),
            )
        )

    return feedbacks


@router.put("/admin/feedback/{feedback_id}", response_model=PlatformFeedbackResponse)
async def update_feedback_status(
    feedback_id: str,
    data: PlatformFeedbackUpdate,
    current_user: Annotated[User, Depends(require_admin)],
):
    """Update feedback status (admin only)."""
    supabase = get_supabase()

    # Check if feedback exists
    existing = (
        supabase.table("platform_feedback")
        .select("*")
        .eq("id", feedback_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zpětná vazba nenalezena",
        )

    update_data = {}
    if data.status is not None:
        update_data["status"] = data.status.value if hasattr(data.status, "value") else data.status
        if data.status in ["in_progress", "done", "rejected"]:
            update_data["handled_by"] = current_user.id
            update_data["handled_at"] = datetime.utcnow().isoformat()
    if data.admin_note is not None:
        update_data["admin_note"] = data.admin_note

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Žádná data k aktualizaci",
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = (
        supabase.table("platform_feedback")
        .update(update_data)
        .eq("id", feedback_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat zpětnou vazbu",
        )

    row = result.data[0]
    return PlatformFeedbackResponse(
        id=row["id"],
        submitted_by=row["submitted_by"],
        submitter_name=get_seller_name(supabase, row["submitted_by"]),
        content=row["content"],
        category=row["category"],
        priority=row["priority"],
        status=row["status"],
        admin_note=row.get("admin_note"),
        handled_by=row.get("handled_by"),
        handler_name=f"{current_user.first_name} {current_user.last_name}".strip() if row.get("handled_by") == current_user.id else get_seller_name(supabase, row.get("handled_by")),
        handled_at=row.get("handled_at"),
        page_url=row.get("page_url"),
        created_at=row.get("created_at"),
    )


@router.get("/admin/feedback/stats")
async def get_feedback_stats(
    current_user: Annotated[User, Depends(require_admin)],
):
    """Get feedback statistics (admin only)."""
    supabase = get_supabase()

    result = (
        supabase.table("platform_feedback")
        .select("status, category, priority")
        .execute()
    )

    stats = {
        "total": 0,
        "by_status": {"open": 0, "in_progress": 0, "done": 0, "rejected": 0},
        "by_category": {"bug": 0, "idea": 0, "ux": 0, "other": 0},
        "by_priority": {"low": 0, "medium": 0, "high": 0},
    }

    for row in result.data or []:
        stats["total"] += 1
        status_val = row.get("status", "open")
        category = row.get("category", "other")
        priority = row.get("priority", "medium")

        if status_val in stats["by_status"]:
            stats["by_status"][status_val] += 1
        if category in stats["by_category"]:
            stats["by_category"][category] += 1
        if priority in stats["by_priority"]:
            stats["by_priority"][priority] += 1

    return stats
