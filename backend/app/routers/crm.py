from datetime import datetime, date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_supabase
from ..dependencies import require_sales_or_admin
from ..schemas.auth import User
from ..schemas.crm import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    BusinessListResponse,
    ActivityCreate,
    ActivityResponse,
    TodayTask,
    TodayTasksResponse,
    CRMStats,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


def get_seller_name(supabase, seller_id: str | None) -> str | None:
    """Get seller name by ID."""
    if not seller_id:
        return None
    result = supabase.table("sellers").select("first_name, last_name").eq("id", seller_id).limit(1).execute()
    if result.data:
        s = result.data[0]
        return f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or None
    return None


def types_to_string(types) -> str | None:
    """Convert types array to comma-separated string."""
    if not types:
        return None
    if isinstance(types, list):
        return ", ".join(types) if types else None
    return str(types)


@router.get("/businesses", response_model=BusinessListResponse)
async def list_businesses(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    status_crm: str | None = Query(None, description="Comma-separated statuses"),
    search: str | None = Query(None, description="Search in name"),
    owner_seller_id: str | None = Query(None, description="Filter by owner seller"),
    next_follow_up_at_before: date | None = Query(None, description="Follow-up before date"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List businesses with filters and pagination. Sales see only their own."""
    supabase = get_supabase()

    # Base query
    query = supabase.table("businesses").select("*", count="exact")

    # RBAC: Sales see only their own or unassigned
    if current_user.role == "sales":
        query = query.or_(f"owner_seller_id.eq.{current_user.id},owner_seller_id.is.null")
    elif owner_seller_id:
        query = query.eq("owner_seller_id", owner_seller_id)

    # Status filter
    if status_crm:
        statuses = [s.strip() for s in status_crm.split(",")]
        query = query.in_("status_crm", statuses)

    # Search filter
    if search:
        query = query.ilike("name", f"%{search}%")

    # Follow-up filter
    if next_follow_up_at_before:
        query = query.lte("next_follow_up_at", next_follow_up_at_before.isoformat())

    # Order by next_follow_up_at (nulls last), then created_at
    query = query.order("next_follow_up_at", nullsfirst=False).order("created_at", desc=True)

    # Pagination
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    # Transform response
    items = []
    for row in result.data:
        items.append(BusinessResponse(
            id=row["id"],
            name=row["name"],
            address=row.get("address_full"),
            phone=row.get("phone"),
            email=row.get("email"),
            website=row.get("website"),
            category=types_to_string(row.get("types")),
            notes=row.get("editorial_summary"),
            status_crm=row.get("status_crm", "new"),
            owner_seller_id=row.get("owner_seller_id"),
            owner_seller_name=get_seller_name(supabase, row.get("owner_seller_id")),
            next_follow_up_at=row.get("next_follow_up_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        ))

    return BusinessListResponse(
        items=items,
        total=result.count or 0,
        page=page,
        limit=limit
    )


@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get a single business by ID."""
    supabase = get_supabase()

    # First fetch the business
    result = supabase.table("businesses").select("*").eq("id", business_id).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )

    row = result.data[0]

    # RBAC check for sales - can only access their own or unassigned
    if current_user.role == "sales":
        owner = row.get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )

    return BusinessResponse(
        id=row["id"],
        name=row["name"],
        address=row.get("address_full"),
        phone=row.get("phone"),
        email=row.get("email"),
        website=row.get("website"),
        category=types_to_string(row.get("types")),
        notes=row.get("editorial_summary"),
        status_crm=row.get("status_crm", "new"),
        owner_seller_id=row.get("owner_seller_id"),
        owner_seller_name=get_seller_name(supabase, row.get("owner_seller_id")),
        next_follow_up_at=row.get("next_follow_up_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.post("/businesses", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    data: BusinessCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new business/lead."""
    supabase = get_supabase()

    # Map fields to database columns
    insert_data = {
        "name": data.name,
        "address_full": data.address,
        "phone": data.phone,
        "email": data.email,
        "website": data.website,
        "types": data.category,
        "editorial_summary": data.notes,
        "status_crm": data.status_crm.value if data.status_crm else "new",
        "owner_seller_id": data.owner_seller_id or (current_user.id if current_user.role == "sales" else None),
    }

    # Convert datetime to ISO string if present
    if data.next_follow_up_at:
        insert_data["next_follow_up_at"] = data.next_follow_up_at.isoformat()

    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    result = supabase.table("businesses").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create business"
        )

    row = result.data[0]
    return BusinessResponse(
        id=row["id"],
        name=row["name"],
        address=row.get("address_full"),
        phone=row.get("phone"),
        email=row.get("email"),
        website=row.get("website"),
        category=types_to_string(row.get("types")),
        notes=row.get("editorial_summary"),
        status_crm=row.get("status_crm", "new"),
        owner_seller_id=row.get("owner_seller_id"),
        owner_seller_name=get_seller_name(supabase, row.get("owner_seller_id")),
        next_follow_up_at=row.get("next_follow_up_at"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.put("/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    data: BusinessUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update a business."""
    supabase = get_supabase()

    # Check access
    existing = supabase.table("businesses").select("id, owner_seller_id").eq("id", business_id).limit(1).execute()

    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    # RBAC check for sales
    if current_user.role == "sales":
        owner = existing.data[0].get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Map fields to database columns
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.address is not None:
        update_data["address_full"] = data.address
    if data.phone is not None:
        update_data["phone"] = data.phone
    if data.email is not None:
        update_data["email"] = data.email
    if data.website is not None:
        update_data["website"] = data.website
    if data.category is not None:
        update_data["types"] = data.category
    if data.notes is not None:
        update_data["editorial_summary"] = data.notes
    if data.status_crm is not None:
        update_data["status_crm"] = data.status_crm.value
    if data.owner_seller_id is not None:
        update_data["owner_seller_id"] = data.owner_seller_id
    if data.next_follow_up_at is not None:
        update_data["next_follow_up_at"] = data.next_follow_up_at.isoformat()

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update")

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = supabase.table("businesses").update(update_data).eq("id", business_id).execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update")

    # Fetch with seller name
    return await get_business(business_id, current_user)


@router.delete("/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Delete a business. Admin can delete any, sales only their own."""
    supabase = get_supabase()

    # Check if business exists and user has permission
    existing = supabase.table("businesses").select("id, owner_seller_id").eq("id", business_id).limit(1).execute()

    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    # RBAC: Sales can only delete their own or unassigned
    if current_user.role == "sales":
        owner = existing.data[0].get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    supabase.table("businesses").delete().eq("id", business_id).execute()


# Activities
@router.get("/businesses/{business_id}/activities", response_model=list[ActivityResponse])
async def list_activities(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    limit: int = Query(50, ge=1, le=100),
):
    """Get activities for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    result = supabase.table("crm_activities").select("*").eq(
        "business_id", business_id
    ).order("occurred_at", desc=True).limit(limit).execute()

    activities = []
    for row in result.data:
        activities.append(ActivityResponse(
            id=row["id"],
            business_id=row["business_id"],
            seller_id=row.get("seller_id", ""),
            seller_name=get_seller_name(supabase, row.get("seller_id")),
            activity_type=row["type"],           # DB column is 'type'
            description=row.get("content", ""),  # DB column is 'content'
            outcome=row.get("outcome"),
            duration_minutes=None,               # Column doesn't exist in DB
            created_at=row.get("occurred_at"),   # Use occurred_at
        ))

    return activities


@router.post("/businesses/{business_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    business_id: str,
    data: ActivityCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Add an activity to a business."""
    supabase = get_supabase()

    # Verify access
    await get_business(business_id, current_user)

    # Map to actual database column names
    insert_data = {
        "business_id": business_id,
        "seller_id": current_user.id,
        "type": data.activity_type.value,  # DB column is 'type'
        "content": data.description,        # DB column is 'content'
        "outcome": data.outcome,
        "occurred_at": datetime.utcnow().isoformat(),  # Required
    }

    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    result = supabase.table("crm_activities").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create activity")

    # Update business status if requested
    if data.new_status:
        supabase.table("businesses").update({
            "status_crm": data.new_status.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", business_id).execute()

    row = result.data[0]
    return ActivityResponse(
        id=row["id"],
        business_id=row["business_id"],
        seller_id=row["seller_id"],
        seller_name=f"{current_user.first_name} {current_user.last_name}",
        activity_type=row["type"],           # DB column is 'type'
        description=row.get("content", ""),  # DB column is 'content'
        outcome=row.get("outcome"),
        duration_minutes=None,               # Column doesn't exist in DB
        created_at=row.get("occurred_at"),   # Use occurred_at
    )


# Dashboard
@router.get("/dashboard/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get today's follow-ups and tasks for the current user."""
    supabase = get_supabase()

    today = date.today().isoformat()

    query = supabase.table("businesses").select(
        "id, name, phone, status_crm, next_follow_up_at"
    ).lte("next_follow_up_at", today).not_.in_(
        "status_crm", ["won", "lost", "dnc"]
    )

    # RBAC
    if current_user.role == "sales":
        query = query.eq("owner_seller_id", current_user.id)

    query = query.order("next_follow_up_at").limit(50)

    result = query.execute()

    tasks = [
        TodayTask(
            id=row["id"],
            business_id=row["id"],
            business_name=row["name"],
            phone=row.get("phone"),
            status_crm=row["status_crm"],
            next_follow_up_at=row.get("next_follow_up_at"),
            last_activity=None
        )
        for row in result.data
    ]

    return TodayTasksResponse(tasks=tasks, total=len(tasks))


@router.get("/dashboard/stats", response_model=CRMStats)
async def get_crm_stats(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get CRM statistics."""
    supabase = get_supabase()

    query = supabase.table("businesses").select("status_crm, next_follow_up_at")

    # RBAC
    if current_user.role == "sales":
        query = query.or_(f"owner_seller_id.eq.{current_user.id},owner_seller_id.is.null")

    result = query.execute()

    today = date.today().isoformat()
    stats = {
        "total_leads": 0,
        "new_leads": 0,
        "calling": 0,
        "interested": 0,
        "offer_sent": 0,
        "won": 0,
        "lost": 0,
        "dnc": 0,
        "follow_ups_today": 0,
    }

    for row in result.data:
        stats["total_leads"] += 1
        status = row.get("status_crm", "new")

        if status == "new":
            stats["new_leads"] += 1
        elif status == "calling":
            stats["calling"] += 1
        elif status == "interested":
            stats["interested"] += 1
        elif status == "offer_sent":
            stats["offer_sent"] += 1
        elif status == "won":
            stats["won"] += 1
        elif status == "lost":
            stats["lost"] += 1
        elif status == "dnc":
            stats["dnc"] += 1

        follow_up = row.get("next_follow_up_at")
        if follow_up and follow_up <= today and status not in ["won", "lost", "dnc"]:
            stats["follow_ups_today"] += 1

    return CRMStats(**stats)


# Projects
@router.get("/businesses/{business_id}/project", response_model=Optional[ProjectResponse])
async def get_project(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get project for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    result = supabase.table("website_projects").select("*").eq(
        "business_id", business_id
    ).limit(1).execute()

    if not result.data:
        return None

    row = result.data[0]
    return ProjectResponse(
        id=row["id"],
        business_id=row["business_id"],
        package=row.get("package", "start"),
        status=row.get("status", "offer"),
        price_setup=row.get("price_setup"),
        price_monthly=row.get("price_monthly"),
        domain=row.get("domain"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.post("/businesses/{business_id}/project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    business_id: str,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a project for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    # Check if project already exists
    existing = supabase.table("website_projects").select("id").eq(
        "business_id", business_id
    ).limit(1).execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Projekt pro tuto firmu již existuje"
        )

    insert_data = {
        "business_id": business_id,
        "package": data.package.value if hasattr(data.package, 'value') else data.package,
        "status": data.status.value if hasattr(data.status, 'value') else data.status,
        "price_setup": data.price_setup,
        "price_monthly": data.price_monthly,
        "domain": data.domain,
        "notes": data.notes,
    }

    result = supabase.table("website_projects").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit projekt"
        )

    row = result.data[0]
    return ProjectResponse(
        id=row["id"],
        business_id=row["business_id"],
        package=row.get("package", "start"),
        status=row.get("status", "offer"),
        price_setup=row.get("price_setup"),
        price_monthly=row.get("price_monthly"),
        domain=row.get("domain"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@router.put("/businesses/{business_id}/project", response_model=ProjectResponse)
async def update_project(
    business_id: str,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update a project."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    # Check if project exists
    existing = supabase.table("website_projects").select("id").eq(
        "business_id", business_id
    ).limit(1).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projekt nenalezen"
        )

    update_data = {}
    if data.package is not None:
        update_data["package"] = data.package.value if hasattr(data.package, 'value') else data.package
    if data.status is not None:
        update_data["status"] = data.status.value if hasattr(data.status, 'value') else data.status
    if data.price_setup is not None:
        update_data["price_setup"] = data.price_setup
    if data.price_monthly is not None:
        update_data["price_monthly"] = data.price_monthly
    if data.domain is not None:
        update_data["domain"] = data.domain
    if data.notes is not None:
        update_data["notes"] = data.notes

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Žádná data k aktualizaci"
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = supabase.table("website_projects").update(update_data).eq(
        "business_id", business_id
    ).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat projekt"
        )

    row = result.data[0]
    return ProjectResponse(
        id=row["id"],
        business_id=row["business_id"],
        package=row.get("package", "start"),
        status=row.get("status", "offer"),
        price_setup=row.get("price_setup"),
        price_monthly=row.get("price_monthly"),
        domain=row.get("domain"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )
