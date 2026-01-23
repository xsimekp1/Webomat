import json
from datetime import datetime, date
from typing import Annotated, Optional
from urllib.request import urlopen

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
    SellerDashboard,
    ARESCompany,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


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


def types_to_string(types) -> str | None:
    """Convert types array to comma-separated string."""
    if not types:
        return None
    if isinstance(types, list):
        return ", ".join(types) if types else None
    return str(types)


@router.get("/ares/{ico}", response_model=ARESCompany)
async def get_company_from_ares(
    ico: str,
    # current_user: Annotated[User, Depends(require_sales_or_admin)], # Temporarily disabled for testing
):
    """
    Fetch company data from ARES (Czech Business Register) by IČO.

    Returns basic company information including name, address, legal form, and DIC.
    """
    # Validate ICO format (8 digits)
    if not ico.isdigit() or len(ico) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="IČO musí být 8 číslic"
        )

    # For now, return mock data for development and testing
    # TODO: Implement actual ARES API call and XML parsing for production

    # Mock response based on ICO
    company_names = {
        "12345678": "Test Firma s.r.o.",
        "87654321": "ABC Corporation a.s.",
        "11111111": "Sample Company spol. s r.o.",
    }

    mock_data = {
        "ico": ico,
        "obchodniJmeno": company_names.get(ico, f"Firma s IČO {ico}"),
        "sidlo": {
            "nazevObce": "Praha",
            "nazevUlice": "Václavské náměstí",
            "cisloDomovni": 68,
            "cisloOrientacni": 1,
            "psc": 11000,
            "textovaAdresa": "Václavské náměstí 68/1, 110 00 Praha",
        },
        "pravniForma": "101",
        "dic": f"CZ{ico}",
    }

    return ARESCompany(**mock_data)

    # For now, return mock data for development and testing
    # TODO: Implement actual ARES API call and XML parsing for production

    # Mock response based on ICO
    company_names = {
        "12345678": "Test Firma s.r.o.",
        "87654321": "ABC Corporation a.s.",
        "11111111": "Sample Company spol. s r.o.",
    }

    mock_data = {
        "ico": ico,
        "obchodniJmeno": company_names.get(ico, f"Firma s IČO {ico}"),
        "sidlo": {
            "nazevObce": "Praha",
            "nazevUlice": "Václavské náměstí",
            "cisloDomovni": 68,
            "cisloOrientacni": 1,
            "psc": 11000,
            "textovaAdresa": "Václavské náměstí 68/1, 110 00 Praha",
        },
        "pravniForma": "101",
        "dic": f"CZ{ico}",
    }

    return ARESCompany(**mock_data)


@router.get("/businesses/check-duplicate")
async def check_duplicate(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    phone: str | None = Query(None, description="Phone to check"),
    website: str | None = Query(None, description="Website to check"),
    place_id: str | None = Query(None, description="Google Place ID to check"),
    name: str | None = Query(None, description="Name to check for similar entries"),
):
    """
    Check if a business with given phone/website/place_id already exists.
    Also returns similar names as warnings (for private persons without IČO).
    """
    supabase = get_supabase()

    # Strict duplicate check (blocks creation)
    duplicate = check_duplicate_business(supabase, phone, website, place_id)
    if duplicate:
        return {
            "is_duplicate": True,
            "existing_business": {
                "id": duplicate["id"],
                "name": duplicate["name"],
                "phone": duplicate.get("phone"),
                "website": duplicate.get("website"),
            },
            "similar_names": [],
        }

    # Soft check by name (warning only, doesn't block)
    similar = []
    if name:
        similar_results = check_similar_by_name(supabase, name)
        similar = [
            {
                "id": s["id"],
                "name": s["name"],
                "phone": s.get("phone"),
                "website": s.get("website"),
                "contact_person": s.get("contact_person"),
            }
            for s in similar_results
        ]

    return {"is_duplicate": False, "existing_business": None, "similar_names": similar}


@router.get("/businesses", response_model=BusinessListResponse)
async def list_businesses(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    status_crm: str | None = Query(None, description="Comma-separated statuses"),
    search: str | None = Query(None, description="Search in name"),
    owner_seller_id: str | None = Query(None, description="Filter by owner seller"),
    next_follow_up_at_before: date | None = Query(
        None, description="Follow-up before date"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List businesses with filters and pagination. Sales see only their own."""
    supabase = get_supabase()

    # Base query
    query = supabase.table("businesses").select("*", count="exact")

    # RBAC: Sales see only their own or unassigned
    if current_user.role == "sales":
        query = query.or_(
            f"owner_seller_id.eq.{current_user.id},owner_seller_id.is.null"
        )
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
    query = query.order("next_follow_up_at", nullsfirst=False).order(
        "created_at", desc=True
    )

    # Pagination
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    # Transform response
    items = []
    for row in result.data:
        items.append(
            BusinessResponse(
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
        )

    return BusinessListResponse(
        items=items, total=result.count or 0, page=page, limit=limit
    )


@router.get("/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get a single business by ID."""
    supabase = get_supabase()

    # First fetch the business
    result = (
        supabase.table("businesses")
        .select("*")
        .eq("id", business_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )

    row = result.data[0]

    # RBAC check for sales - can only access their own or unassigned
    if current_user.role == "sales":
        owner = row.get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
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


def check_duplicate_business(
    supabase, phone: str | None, website: str | None, place_id: str | None = None
) -> dict | None:
    """Check if business already exists by phone, website, or place_id. Returns existing business or None."""
    if place_id:
        result = (
            supabase.table("businesses")
            .select("id, name, phone, website")
            .eq("place_id", place_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

    if phone:
        # Normalize phone - remove spaces and common prefixes for comparison
        normalized_phone = phone.replace(" ", "").replace("-", "")
        result = (
            supabase.table("businesses")
            .select("id, name, phone, website")
            .ilike("phone", f"%{normalized_phone[-9:]}%")
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

    if website:
        # Normalize website - remove protocol and www
        normalized_web = (
            website.lower()
            .replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .rstrip("/")
        )
        result = (
            supabase.table("businesses")
            .select("id, name, phone, website")
            .ilike("website", f"%{normalized_web}%")
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]


def check_similar_by_name(supabase, name: str) -> list[dict]:
    """
    Check for businesses with similar names (for private persons without IČO).
    Returns list of potential matches (warning, not blocking).
    """
    if not name or len(name) < 3:
        return []

    # Search by exact name match or similar
    result = (
        supabase.table("businesses")
        .select("id, name, phone, website, contact_person")
        .ilike("name", f"%{name}%")
        .limit(5)
        .execute()
    )
    return result.data if result.data else []


@router.post(
    "/businesses", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED
)
async def create_business(
    data: BusinessCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new business/lead."""
    supabase = get_supabase()

    # Check for duplicates
    duplicate = check_duplicate_business(supabase, data.phone, data.website)
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Firma již existuje v systému: {duplicate['name']} (ID: {duplicate['id']})",
        )

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
        "owner_seller_id": data.owner_seller_id
        or (current_user.id if current_user.role == "sales" else None),
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
            detail="Failed to create business",
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
    existing = (
        supabase.table("businesses")
        .select("id, owner_seller_id")
        .eq("id", business_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )

    # RBAC check for sales
    if current_user.role == "sales":
        owner = existing.data[0].get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update"
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = (
        supabase.table("businesses").update(update_data).eq("id", business_id).execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update"
        )

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
    existing = (
        supabase.table("businesses")
        .select("id, owner_seller_id")
        .eq("id", business_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )

    # RBAC: Sales can only delete their own or unassigned
    if current_user.role == "sales":
        owner = existing.data[0].get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    supabase.table("businesses").delete().eq("id", business_id).execute()


# Activities
@router.get(
    "/businesses/{business_id}/activities", response_model=list[ActivityResponse]
)
async def list_activities(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    limit: int = Query(50, ge=1, le=100),
):
    """Get activities for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    result = (
        supabase.table("crm_activities")
        .select("*")
        .eq("business_id", business_id)
        .order("occurred_at", desc=True)
        .limit(limit)
        .execute()
    )

    activities = []
    for row in result.data:
        activities.append(
            ActivityResponse(
                id=row["id"],
                business_id=row["business_id"],
                seller_id=row.get("seller_id", ""),
                seller_name=get_seller_name(supabase, row.get("seller_id")),
                activity_type=row["type"],  # DB column is 'type'
                description=row.get("content", ""),  # DB column is 'content'
                outcome=row.get("outcome"),
                duration_minutes=None,  # Column doesn't exist in DB
                created_at=row.get("occurred_at"),  # Use occurred_at
            )
        )

    return activities


@router.post(
    "/businesses/{business_id}/activities",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
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
        "content": data.description,  # DB column is 'content'
        "outcome": data.outcome,
        "occurred_at": datetime.utcnow().isoformat(),  # Required
    }

    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    result = supabase.table("crm_activities").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create activity",
        )

    # Update business status if requested
    if data.new_status:
        supabase.table("businesses").update(
            {
                "status_crm": data.new_status.value,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", business_id).execute()

    row = result.data[0]
    return ActivityResponse(
        id=row["id"],
        business_id=row["business_id"],
        seller_id=row["seller_id"],
        seller_name=f"{current_user.first_name} {current_user.last_name}",
        activity_type=row["type"],  # DB column is 'type'
        description=row.get("content", ""),  # DB column is 'content'
        outcome=row.get("outcome"),
        duration_minutes=None,  # Column doesn't exist in DB
        created_at=row.get("occurred_at"),  # Use occurred_at
    )


# Dashboard
@router.get("/dashboard/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get today's follow-ups and tasks for the current user."""
    supabase = get_supabase()

    today = date.today().isoformat()

    query = (
        supabase.table("businesses")
        .select("id, name, phone, status_crm, next_follow_up_at")
        .lte("next_follow_up_at", today)
        .not_.in_("status_crm", ["won", "lost", "dnc"])
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
            last_activity=None,
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
        query = query.or_(
            f"owner_seller_id.eq.{current_user.id},owner_seller_id.is.null"
        )

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
@router.get("/businesses/{business_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get all projects for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    result = (
        supabase.table("website_projects")
        .select("*")
        .eq("business_id", business_id)
        .order("created_at", desc=True)
        .execute()
    )

    projects = []
    for row in result.data:
        projects.append(
            ProjectResponse(
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
        )
    return projects


@router.post(
    "/businesses/{business_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    business_id: str,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a project for a business."""
    supabase = get_supabase()

    # Verify access to business
    await get_business(business_id, current_user)

    insert_data = {
        "business_id": business_id,
        "package": data.package.value
        if hasattr(data.package, "value")
        else data.package,
        "status": data.status.value if hasattr(data.status, "value") else data.status,
        "price_setup": data.price_setup,
        "price_monthly": data.price_monthly,
        "domain": data.domain,
        "notes": data.notes,
    }

    result = supabase.table("website_projects").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit projekt",
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


@router.get("/sellers", response_model=list[dict])
async def get_sellers_list(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get list of all sellers for UI dropdowns and caching."""
    supabase = get_supabase()

    # Only admin can see all sellers, sales see themselves + other active sellers
    if current_user.role == "admin":
        result = (
            supabase.table("sellers")
            .select("id, first_name, last_name, email, role, is_active")
            .execute()
        )
    else:
        # Sales see themselves and other active sellers
        result = (
            supabase.table("sellers")
            .select("id, first_name, last_name, email, role, is_active")
            .eq("is_active", True)
            .execute()
        )

    sellers = []
    for seller in result.data or []:
        sellers.append(
            {
                "id": seller["id"],
                "name": f"{seller.get('first_name', '')} {seller.get('last_name', '')}".strip()
                or seller.get("email", ""),
                "email": seller.get("email"),
                "role": seller.get("role"),
                "is_active": seller.get("is_active", True),
            }
        )

    return sellers


@router.get("/seller/dashboard", response_model=SellerDashboard)
async def get_seller_dashboard(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get dashboard data for seller including available balance and pending amounts."""
    supabase = get_supabase()

    # Calculate available balance: sum of earned commissions minus payouts
    earned_result = (
        supabase.table("ledger_entries")
        .select("amount")
        .eq("seller_id", current_user.id)
        .eq("type", "commission_earned")
        .execute()
    )
    total_earned = (
        sum(row["amount"] for row in earned_result.data) if earned_result.data else 0
    )

    payout_result = (
        supabase.table("ledger_entries")
        .select("amount")
        .eq("seller_id", current_user.id)
        .in_("type", ["payout_reserved", "payout_paid"])
        .execute()
    )
    total_payouts = (
        sum(row["amount"] for row in payout_result.data) if payout_result.data else 0
    )

    available_balance = total_earned - total_payouts

    # Calculate pending projects amount: sum of project prices where status is won/in_production
    projects_result = (
        supabase.table("website_projects")
        .select("price_setup, price_monthly, status")
        .eq("seller_id", current_user.id)
        .in_("status", ["won", "in_production"])
        .execute()
    )
    pending_amount = 0
    if projects_result.data:
        for project in projects_result.data:
            if project["price_setup"]:
                pending_amount += project["price_setup"]
            # Could add monthly if needed

    # Get recent invoices
    invoices_result = (
        supabase.table("invoices")
        .select("id, invoice_number, amount_total, status, issue_date")
        .eq("seller_id", current_user.id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    recent_invoices = invoices_result.data if invoices_result.data else []

    # Weekly rewards (simplified - last 4 weeks of commissions)
    # For now, placeholder - would need proper date aggregation
    weekly_rewards = [
        {"week": "This week", "amount": 0},
        {"week": "Last week", "amount": 0},
        {"week": "2 weeks ago", "amount": 0},
        {"week": "3 weeks ago", "amount": 0},
    ]

    return SellerDashboard(
        available_balance=available_balance,
        pending_projects_amount=pending_amount,
        recent_invoices=recent_invoices,
        weekly_rewards=weekly_rewards,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update a project by ID."""
    supabase = get_supabase()

    # Check if project exists and get business_id for access check
    existing = (
        supabase.table("website_projects")
        .select("id, business_id")
        .eq("id", project_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Verify access to business
    await get_business(existing.data[0]["business_id"], current_user)

    update_data = {}
    if data.package is not None:
        update_data["package"] = (
            data.package.value if hasattr(data.package, "value") else data.package
        )
    if data.status is not None:
        update_data["status"] = (
            data.status.value if hasattr(data.status, "value") else data.status
        )
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Žádná data k aktualizaci"
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = (
        supabase.table("website_projects")
        .update(update_data)
        .eq("id", project_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat projekt",
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
