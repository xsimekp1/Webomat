import json
from datetime import datetime, date, timedelta
from typing import Annotated, Optional
from urllib.request import urlopen
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    File,
    UploadFile,
    Body,
)
from fastapi.responses import Response

from ..database import get_supabase
from ..dependencies import require_sales_or_admin, require_admin
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
    PendingProjectInfo,
    UnpaidClientInvoice,
    ARESCompany,
    WebsiteVersionCreate,
    WebsiteVersionResponse,
    WebsiteVersionListResponse,
    ProjectAssetCreate,
    ProjectAssetResponse,
    BalancePageResponse,
    LedgerEntryResponse,
    WeeklyRewardSummary,
    InvoiceIssuedCreate,
    InvoiceIssuedResponse,
    InvoiceStatusUpdate,
    InvoiceRejectRequest,
    AdminInvoiceListItem,
    AdminInvoiceListResponse,
    SellerClaimsResponse,
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
                ico=row.get("ico"),
                dic=row.get("dic"),
                billing_address=row.get("billing_address"),
                bank_account=row.get("bank_account"),
                contact_person=row.get("contact_person"),
                logo_url=row.get("logo_url"),
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
        ico=row.get("ico"),
        dic=row.get("dic"),
        billing_address=row.get("billing_address"),
        bank_account=row.get("bank_account"),
        contact_person=row.get("contact_person"),
        logo_url=row.get("logo_url"),
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
    # NOTE: next_follow_up_at is intentionally NOT updatable directly
    # It can only be set through activities (crm_activities table)

    # Fakturační údaje
    if data.ico is not None:
        update_data["ico"] = data.ico
    if data.dic is not None:
        update_data["dic"] = data.dic
    if data.billing_address is not None:
        update_data["billing_address"] = data.billing_address
    if data.bank_account is not None:
        update_data["bank_account"] = data.bank_account
    if data.contact_person is not None:
        update_data["contact_person"] = data.contact_person
    if data.logo_url is not None:
        update_data["logo_url"] = data.logo_url

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


@router.post("/businesses/{business_id}/logo", response_model=dict)
async def upload_business_logo(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    file: UploadFile = File(...),
):
    """Upload logo for a business. Returns the public URL of the uploaded file."""
    supabase = get_supabase()

    # Check access and ownership
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

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image"
        )

    # Validate file size (max 5MB)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB",
        )

    try:
        # Generate unique filename
        import uuid
        import os

        file_extension = os.path.splitext(file.filename or "")[1] or ".jpg"
        unique_filename = f"business_logos/{business_id}/{uuid.uuid4()}{file_extension}"

        # Upload to Supabase Storage
        storage_result = supabase.storage.from_("webomat").upload(
            path=unique_filename,
            data=await file.read(),
            file_options={"content-type": file.content_type, "upsert": "true"},
        )

        if storage_result.data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage",
            )

        # Get public URL
        public_url = supabase.storage.from_("webomat").get_public_url(unique_filename)

        # Update business record with logo URL
        supabase.table("businesses").update(
            {"logo_url": public_url, "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", business_id).execute()

        return {"logo_url": public_url, "message": "Logo uploaded successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading logo: {str(e)}",
        )


@router.delete("/businesses/{business_id}/logo", response_model=dict)
async def delete_business_logo(
    business_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Remove logo from a business."""
    supabase = get_supabase()

    # Check access and ownership
    existing = (
        supabase.table("businesses")
        .select("id, owner_seller_id, logo_url")
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

    try:
        # Remove logo URL from business record
        supabase.table("businesses").update(
            {"logo_url": None, "updated_at": datetime.utcnow().isoformat()}
        ).eq("id", business_id).execute()

        return {"message": "Logo removed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing logo: {str(e)}",
        )


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

    # Update business status and follow-up if requested
    business_update_data = {}
    if data.new_status:
        business_update_data["status_crm"] = data.new_status.value

    if data.next_follow_up_at:
        # Handle both string and datetime inputs
        if isinstance(data.next_follow_up_at, str):
            # Convert string from datetime-local input to proper datetime format
            business_update_data["next_follow_up_at"] = data.next_follow_up_at
        else:
            business_update_data["next_follow_up_at"] = (
                data.next_follow_up_at.isoformat()
            )

    if business_update_data:
        business_update_data["updated_at"] = datetime.utcnow().isoformat()
        supabase.table("businesses").update(business_update_data).eq(
            "id", business_id
        ).execute()

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
        # Fetch latest version thumbnail if project has versions
        latest_thumbnail_url = None
        latest_version_id = row.get("latest_version_id")
        versions_count = row.get("versions_count", 0)

        if latest_version_id:
            version_result = (
                supabase.table("website_versions")
                .select("thumbnail_url")
                .eq("id", latest_version_id)
                .limit(1)
                .execute()
            )
            if version_result.data:
                latest_thumbnail_url = version_result.data[0].get("thumbnail_url")

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
                versions_count=versions_count,
                latest_version_id=latest_version_id,
                latest_thumbnail_url=latest_thumbnail_url,
                seller_id=row.get("seller_id"),
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
        "seller_id": current_user.id,
        "business_id": business_id,
        "package": str(data.package.value)
        if hasattr(data.package, "value")
        else str(data.package),
        "status": str(data.status.value)
        if hasattr(data.status, "value")
        else str(data.status),
        "price_setup": data.price_setup,
        "price_monthly": data.price_monthly,
        "domain": data.domain,
        "notes": data.notes,
    }

    try:
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
            seller_id=row.get("seller_id"),
            updated_at=row.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        print(f"Project creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při vytváření projektu: {str(e)}",
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
    """Get dashboard data for seller including available balance, pending projects, unpaid invoices."""
    supabase = get_supabase()
    today = date.today()

    # Calculate available balance: sum of all ledger entries
    # Positive entries: commission_earned, admin_adjustment
    # Negative entries: payout_reserved, payout_paid (stored as negative amounts)
    ledger_result = (
        supabase.table("ledger_entries")
        .select("amount, entry_type")
        .eq("seller_id", current_user.id)
        .execute()
    )

    available_balance = 0
    if ledger_result.data:
        for entry in ledger_result.data:
            # All amounts are already signed (positive for earned, negative for payouts)
            available_balance += entry.get("amount", 0)

    # Get businesses owned by this seller OR without owner (accessible to all)
    businesses_result = (
        supabase.table("businesses")
        .select("id, name, status_crm, next_follow_up_at, owner_seller_id")
        .or_(f"owner_seller_id.eq.{current_user.id},owner_seller_id.is.null")
        .execute()
    )
    businesses_data = businesses_result.data if businesses_result.data else []
    business_ids = [b["id"] for b in businesses_data]
    business_names = {b["id"]: b["name"] for b in businesses_data}

    # Count leads and follow-ups
    total_leads = len(businesses_data)
    today_str = today.isoformat()
    follow_ups_today = sum(
        1
        for b in businesses_data
        if b.get("next_follow_up_at")
        and b["next_follow_up_at"][:10]
        <= today_str  # Compare only date part (YYYY-MM-DD)
        and b.get("status_crm") not in ["won", "lost", "dnc"]
    )

    # Get pending projects (offer, won, in_production - not live/cancelled/delivered)
    pending_projects: list[PendingProjectInfo] = []
    pending_amount = 0

    # Get projects from businesses owned by this seller or without owner
    if business_ids:
        projects_result = (
            supabase.table("website_projects")
            .select(
                "id, business_id, seller_id, status, package, price_setup, created_at"
            )
            .in_("business_id", business_ids)
            .in_("status", ["offer", "won", "in_production"])
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
    else:
        projects_result = type("obj", (object,), {"data": []})()

    # Also get projects where seller_id matches (even if business not owned by this seller)
    seller_projects_result = (
        supabase.table("website_projects")
        .select("id, business_id, seller_id, status, package, price_setup, created_at")
        .eq("seller_id", current_user.id)
        .in_("status", ["offer", "won", "in_production"])
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    # Merge and deduplicate projects
    all_projects: dict = {}
    for p in (projects_result.data or []) + (seller_projects_result.data or []):
        if p["id"] not in all_projects:
            all_projects[p["id"]] = p

    # Sort by created_at desc and limit
    projects_data = sorted(
        all_projects.values(), key=lambda x: x.get("created_at", ""), reverse=True
    )[:10]

    # Get business names for projects found via seller_id (might not be in business_names yet)
    missing_business_ids = [
        p["business_id"]
        for p in projects_data
        if p["business_id"] not in business_names
    ]
    if missing_business_ids:
        extra_businesses = (
            supabase.table("businesses")
            .select("id, name")
            .in_("id", missing_business_ids)
            .execute()
        )
        for b in extra_businesses.data or []:
            business_names[b["id"]] = b["name"]

    # Process projects
    for project in projects_data:
        if project.get("price_setup"):
            pending_amount += project["price_setup"]

        # Get latest version for this project
        version_result = (
            supabase.table("website_versions")
            .select("version_number, created_at")
            .eq("project_id", project["id"])
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )

        latest_version = None
        latest_version_date = None
        if version_result.data:
            latest_version = version_result.data[0]["version_number"]
            latest_version_date = version_result.data[0]["created_at"]

        pending_projects.append(
            PendingProjectInfo(
                id=project["id"],
                business_id=project["business_id"],
                business_name=business_names.get(
                    project["business_id"], "Neznámá firma"
                ),
                status=project["status"],
                package=project.get("package", "start"),
                latest_version_number=latest_version,
                latest_version_date=latest_version_date,
            )
        )

    # Get unpaid client invoices (invoices_issued with status issued or overdue)
    unpaid_client_invoices: list[UnpaidClientInvoice] = []

    if business_ids:
        invoices_issued_result = (
            supabase.table("invoices_issued")
            .select("id, business_id, invoice_number, amount_total, due_date, status")
            .in_("business_id", business_ids)
            .in_("status", ["issued", "overdue"])
            .order("due_date")
            .limit(10)
            .execute()
        )

        if invoices_issued_result.data:
            for inv in invoices_issued_result.data:
                due_date = (
                    datetime.fromisoformat(inv["due_date"])
                    if inv.get("due_date")
                    else datetime.now()
                )
                days_overdue = (today - due_date.date()).days

                unpaid_client_invoices.append(
                    UnpaidClientInvoice(
                        id=inv["id"],
                        business_id=inv["business_id"],
                        business_name=business_names.get(
                            inv["business_id"], "Neznámá firma"
                        ),
                        invoice_number=inv["invoice_number"],
                        amount_total=inv["amount_total"],
                        due_date=due_date,
                        days_overdue=days_overdue,
                    )
                )

    # Get recent invoices (invoices_received = invoices from sellers for commissions)
    invoices_result = (
        supabase.table("invoices_received")
        .select("id, invoice_number, amount_total, status, issue_date")
        .eq("seller_id", current_user.id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    recent_invoices = invoices_result.data if invoices_result.data else []

    # Weekly rewards (placeholder)
    weekly_rewards = [
        {"week": "Tento týden", "amount": 0},
        {"week": "Minulý týden", "amount": 0},
        {"week": "Před 2 týdny", "amount": 0},
        {"week": "Před 3 týdny", "amount": 0},
    ]

    return SellerDashboard(
        available_balance=available_balance,
        pending_projects_amount=pending_amount,
        recent_invoices=recent_invoices,
        weekly_rewards=weekly_rewards,
        pending_projects=pending_projects,
        unpaid_client_invoices=unpaid_client_invoices,
        total_leads=total_leads,
        follow_ups_today=follow_ups_today,
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


# Website Versions
@router.get(
    "/projects/{project_id}/versions", response_model=WebsiteVersionListResponse
)
async def list_website_versions(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get all versions for a project."""
    supabase = get_supabase()

    # Verify access to project
    project_result = (
        supabase.table("website_projects")
        .select("business_id")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Check access to business
    await get_business(project_result.data["business_id"], current_user)

    result = (
        supabase.table("website_versions")
        .select("*")
        .eq("project_id", project_id)
        .order("version_number", desc=True)
        .execute()
    )

    versions = []
    for row in result.data or []:
        versions.append(
            WebsiteVersionResponse(
                id=row["id"],
                project_id=row["project_id"],
                version_number=row["version_number"],
                status=row.get("status", "created"),
                source_bundle_path=row.get("source_bundle_path"),
                preview_image_path=row.get("preview_image_path"),
                notes=row.get("notes"),
                created_at=row.get("created_at"),
                created_by=row.get("created_by"),
            )
        )

    return WebsiteVersionListResponse(items=versions, total=len(versions))


@router.post(
    "/projects/{project_id}/versions",
    response_model=WebsiteVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_website_version(
    project_id: str,
    data: WebsiteVersionCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new website version for a project."""
    supabase = get_supabase()

    # Verify access to project
    project_result = (
        supabase.table("website_projects")
        .select("business_id")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Check access to business
    await get_business(project_result.data["business_id"], current_user)

    # Get next version number
    version_result = (
        supabase.table("website_versions")
        .select("version_number")
        .eq("project_id", project_id)
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )

    next_version = 1
    if version_result.data and version_result.data[0]:
        next_version = version_result.data[0]["version_number"] + 1

    # Create version
    insert_data = {
        "project_id": project_id,
        "version_number": next_version,
        "status": "created",
        "source_bundle_path": data.source_bundle_path,
        "preview_image_path": data.preview_image_path,
        "notes": data.notes,
        "created_by": current_user.id,
    }

    result = supabase.table("website_versions").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit verzi",
        )

    row = result.data[0]
    return WebsiteVersionResponse(
        id=row["id"],
        project_id=row["project_id"],
        version_number=row["version_number"],
        status=row.get("status", "created"),
        source_bundle_path=row.get("source_bundle_path"),
        preview_image_path=row.get("preview_image_path"),
        notes=row.get("notes"),
        created_at=row.get("created_at"),
        created_by=row.get("created_by"),
    )


@router.get("/versions/{version_id}", response_model=WebsiteVersionResponse)
async def get_website_version(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get a specific website version."""
    supabase = get_supabase()

    result = (
        supabase.table("website_versions")
        .select("*, website_projects(business_id)")
        .eq("id", version_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verze nenalezena"
        )

    # Check access to business
    business_id = result.data["website_projects"]["business_id"]
    await get_business(business_id, current_user)

    return WebsiteVersionResponse(
        id=result.data["id"],
        project_id=result.data["project_id"],
        version_number=result.data["version_number"],
        status=result.data.get("status", "created"),
        source_bundle_path=result.data.get("source_bundle_path"),
        preview_image_path=result.data.get("preview_image_path"),
        notes=result.data.get("notes"),
        created_at=result.data.get("created_at"),
        created_by=result.data.get("created_by"),
    )


# Project Assets
@router.get("/projects/{project_id}/assets", response_model=list[ProjectAssetResponse])
async def list_project_assets(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get all assets for a project."""
    supabase = get_supabase()

    # Verify access to project
    project_result = (
        supabase.table("website_projects")
        .select("business_id")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Check access to business
    await get_business(project_result.data["business_id"], current_user)

    result = (
        supabase.table("project_assets")
        .select("*")
        .eq("project_id", project_id)
        .order("uploaded_at", desc=True)
        .execute()
    )

    assets = []
    for row in result.data or []:
        assets.append(
            ProjectAssetResponse(
                id=row["id"],
                project_id=row["project_id"],
                type=row["type"],
                file_path=row["file_path"],
                filename=row["filename"],
                mime_type=row["mime_type"],
                size_bytes=row["size_bytes"],
                uploaded_at=row.get("uploaded_at"),
                uploaded_by=row.get("uploaded_by"),
            )
        )

    return assets


# Invoice reminder generation
@router.post("/invoices/{invoice_id}/generate-reminder")
async def generate_payment_reminder(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Generate payment reminder text for an unpaid invoice."""
    supabase = get_supabase()

    # Get invoice details
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nebyla nalezena"
        )

    invoice = invoice_result.data

    # Get business details
    business_result = (
        supabase.table("businesses")
        .select("name, contact_person")
        .eq("id", invoice["business_id"])
        .single()
        .execute()
    )

    if not business_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Klient nebyl nalezen"
        )

    business = business_result.data

    # Get project details if available
    project = None
    if invoice.get("project_id"):
        project_result = (
            supabase.table("website_projects")
            .select("domain, delivered_at")
            .eq("id", invoice["project_id"])
            .single()
            .execute()
        )
        if project_result.data:
            project = project_result.data

    # Generate reminder text
    business_name = business.get("name", "")
    domain = project.get("domain", "") if project else ""
    delivered_date = project.get("delivered_at", "") if project else ""
    due_date = invoice.get("due_date", "")
    invoice_number = invoice.get("invoice_number", "")
    amount_total = invoice.get("amount_total", 0)

    reminder_text = f"""
Dobrý den,

tímto Vám zasíláme upomínku na neuhrazenou fakturu.

Faktura číslo: {invoice_number}
Částka k úhradě: {amount_total} Kč
Datum splatnosti: {due_date}

Informace o našich službách:
Klient: {business_name}
{"Doména: " + domain if domain else "Nepřiděno"}
{"Datum doručení: " + delivered_date[:10] if delivered_date else "Probíhající"}

V případě, že fakturu již uhradil(a) jste, považujte tuto zprávu za bezpředmětnou.

V případě dotazů nás kontaktujte na email nebo telefon.

S pozdravem,
Webomat team
    """.strip()

    return {
        "invoice_id": invoice_id,
        "reminder_text": reminder_text,
        "business_name": business_name,
        "domain": domain,
        "due_date": due_date,
        "amount_total": amount_total,
        "invoice_number": invoice_number,
    }


@router.post("/invoices/{invoice_id}/send-reminder")
async def send_payment_reminder(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Send payment reminder and create follow-up activity."""
    supabase = get_supabase()

    # Generate reminder
    reminder_data = await generate_payment_reminder(invoice_id, current_user)

    # Get follow-up settings (default 3 days)
    settings_result = (
        supabase.table("platform_settings")
        .select("value")
        .eq("key", "follow_up_reminder_days")
        .single()
        .execute()
    )

    follow_up_days = 3  # Default
    if settings_result.data and settings_result.data.get("value"):
        follow_up_days = settings_result.data["value"]

    # Create follow-up activity
    from datetime import datetime, timedelta

    follow_up_date = (datetime.now() + timedelta(days=follow_up_days)).isoformat()

    activity_data = {
        "business_id": reminder_data["business_id"],
        "type": "email",
        "content": f"Odeslána upomínka na fakturu {reminder_data['invoice_number']}",
        "outcome": f"Follow-up za {follow_up_days} dní",
        "occurred_at": datetime.now().isoformat(),
    }

    supabase.table("crm_activities").insert(activity_data).execute()

    # Update business follow-up
    supabase.table("businesses").update(
        {"next_follow_up_at": follow_up_date, "updated_at": datetime.now().isoformat()}
    ).eq("id", reminder_data["business_id"]).execute()

    return {
        "message": "Upomínka byla úspěšně odeslána",
        "follow_up_date": follow_up_date,
        "reminder_text": reminder_data["reminder_text"],
    }


@router.post(
    "/projects/{project_id}/assets",
    response_model=ProjectAssetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_asset(
    project_id: str,
    data: ProjectAssetCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new asset for a project."""
    supabase = get_supabase()

    # Verify access to project
    project_result = (
        supabase.table("website_projects")
        .select("business_id")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Check access to business
    await get_business(project_result.data["business_id"], current_user)

    # Create asset
    insert_data = {
        "project_id": project_id,
        "type": data.type,
        "file_path": data.file_path,
        "filename": data.filename,
        "mime_type": data.mime_type,
        "size_bytes": data.size_bytes,
        "uploaded_by": current_user.id,
    }

    result = supabase.table("project_assets").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit asset",
        )

    row = result.data[0]
    return ProjectAssetResponse(
        id=row["id"],
        project_id=row["project_id"],
        type=row["type"],
        file_path=row["file_path"],
        filename=row["filename"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        uploaded_at=row.get("uploaded_at"),
        uploaded_by=row.get("uploaded_by"),
    )


@router.get("/seller/account/ledger", response_model=BalancePageResponse)
async def get_seller_account_ledger(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    range: str = Query("all", description="Časový rozsah: all/month/quarter/year"),
    type: str = Query("all", description="Typ: all/earned/payout/adjustment"),
    status: str = Query("all", description="Status: all/pending/approved/paid"),
):
    """Get seller account ledger with detailed entries and balance calculation."""
    supabase = get_supabase()

    # Build filters
    entry_type_filter = []
    if type == "earned":
        entry_type_filter = ["commission_earned"]
    elif type == "payout":
        entry_type_filter = ["payout_reserved", "payout_paid"]
    elif type == "adjustment":
        entry_type_filter = ["admin_adjustment"]

    # Get ledger entries with filters
    query = (
        supabase.table("ledger_entries").select("*").eq("seller_id", current_user.id)
    )

    if entry_type_filter:
        query = query.in_("entry_type", entry_type_filter)

    # Apply date range filter
    if range != "all":
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        if range == "month":
            start_date = (now - timedelta(days=30)).isoformat()
        elif range == "quarter":
            start_date = (now - timedelta(days=90)).isoformat()
        elif range == "year":
            start_date = (now - timedelta(days=365)).isoformat()
        else:
            start_date = None

        if start_date:
            query = query.gte("created_at", start_date)

    # Apply status filter for payout entries
    if status != "all":
        query = query.eq("status", status)

    # Execute query
    result = query.order("created_at", desc=True).execute()

    # Calculate available balance: sum of all ledger entries
    # All amounts are signed (positive for earned/adjustment, negative for payouts)
    all_ledger_result = (
        supabase.table("ledger_entries")
        .select("amount")
        .eq("seller_id", current_user.id)
        .execute()
    )

    available_balance = sum(
        entry.get("amount", 0) for entry in (all_ledger_result.data or [])
    )

    # Convert to response format
    ledger_entries = []
    for entry in result.data or []:
        ledger_entries.append(
            LedgerEntryResponse(
                id=entry["id"],
                seller_id=entry["seller_id"],
                entry_type=entry["entry_type"],
                amount=entry["amount"],
                related_invoice_id=entry.get("related_invoice_id"),
                related_project_id=entry.get("related_project_id"),
                related_business_id=entry.get("related_business_id"),
                description=entry.get("description"),
                notes=entry.get("notes"),
                is_test=entry.get("is_test", False),
                created_at=entry.get("created_at"),
                created_by=entry.get("created_by"),
            )
        )

    # Generate weekly rewards summary (simplified)
    weekly_rewards = []
    if range in ["all", "quarter", "year"]:
        # Get last 12 weeks of data
        for i in range(12):
            week_date = datetime.utcnow() - timedelta(weeks=i)
            week_start = week_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=week_date.weekday())
            week_end = week_start + timedelta(days=6)

            week_result = (
                supabase.table("ledger_entries")
                .select("amount")
                .eq("seller_id", current_user.id)
                .eq("entry_type", "commission_earned")
                .gte("created_at", week_start.isoformat())
                .lte("created_at", week_end.isoformat())
                .execute()
            )

            week_total = sum(
                entry.get("amount", 0) for entry in (week_result.data or [])
            )
            if week_total > 0:
                weekly_rewards.append(
                    WeeklyRewardSummary(
                        week_start=week_start, week_end=week_end, amount=week_total
                    )
                )

    return BalancePageResponse(
        available_balance=available_balance,
        ledger_entries=ledger_entries,
        weekly_rewards=weekly_rewards,
    )


# ============================================
# Invoice Management Endpoints
# ============================================


@router.get(
    "/projects/{project_id}/invoices", response_model=list[InvoiceIssuedResponse]
)
async def list_project_invoices(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get all invoices for a project."""
    supabase = get_supabase()

    # Verify access to project
    project_result = (
        supabase.table("website_projects")
        .select("business_id")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    # Check access to business
    await get_business(project_result.data["business_id"], current_user)

    # Get invoices
    result = (
        supabase.table("invoices_issued")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at", desc=True)
        .execute()
    )

    # Get business name
    business_result = (
        supabase.table("businesses")
        .select("name")
        .eq("id", project_result.data["business_id"])
        .single()
        .execute()
    )
    business_name = business_result.data.get("name") if business_result.data else None

    invoices = []
    for row in result.data or []:
        invoices.append(
            InvoiceIssuedResponse(
                id=row["id"],
                business_id=row["business_id"],
                project_id=row.get("project_id"),
                seller_id=row.get("seller_id"),
                invoice_number=row["invoice_number"],
                issue_date=row["issue_date"],
                due_date=row["due_date"],
                paid_date=row.get("paid_date"),
                amount_without_vat=row.get("amount_without_vat", 0),
                vat_rate=row.get("vat_rate", 21),
                vat_amount=row.get("vat_amount"),
                amount_total=row["amount_total"],
                currency=row.get("currency", "CZK"),
                payment_type=row.get("payment_type", "setup"),
                status=row["status"],
                description=row.get("description"),
                variable_symbol=row.get("variable_symbol"),
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
                business_name=business_name,
            )
        )

    return invoices


@router.put("/businesses/{business_id}/status", response_model=dict)
async def update_business_status(
    business_id: str,
    status_data: dict,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update business CRM status."""
    supabase = get_supabase()

    # Get current business
    result = (
        supabase.table("businesses")
        .select("*")
        .eq("id", business_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Business not found")

    business = result.data
    current_status = business["status_crm"]

    # Check access to business
    await get_business(business_id, current_user)

    new_status = status_data.get("status", "")

    # Validate status change - only allow to change to "designed" from specific statuses
    allowed_from_statuses = ["new", "calling", "interested"]
    if new_status == "designed" and current_status not in allowed_from_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from '{current_status}' to 'designed'",
        )

    # Update business status
    update_data = {
        "status_crm": new_status,
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = (
        supabase.table("businesses").update(update_data).eq("id", business_id).execute()
    )

    return {"message": f"Status updated to '{new_status}'"}


@router.get("/invoices-issued/{invoice_id}", response_model=InvoiceIssuedResponse)
async def get_invoice_detail(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get invoice detail by ID."""
    supabase = get_supabase()

    result = (
        supabase.table("invoices_issued")
        .select("*, businesses!inner(name)")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = result.data
    business_name = invoice.get("businesses", {}).get("name", "Unknown Business")

    # RBAC Check - use business-centric access control like other CRM functions
    if current_user.role == "sales":
        # Get the business for this invoice
        business_result = (
            supabase.table("businesses")
            .select("owner_seller_id")
            .eq("id", invoice["business_id"])
            .single()
            .execute()
        )

        if business_result.data:
            owner = business_result.data.get("owner_seller_id")
            if owner and owner != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")

    return InvoiceIssuedResponse(
        id=invoice["id"],
        business_id=invoice["business_id"],
        project_id=invoice.get("project_id"),
        seller_id=invoice.get("seller_id"),
        invoice_number=invoice["invoice_number"],
        issue_date=invoice["issue_date"],
        due_date=invoice["due_date"],
        paid_date=invoice.get("paid_date"),
        amount_without_vat=invoice.get("amount_without_vat", 0),
        vat_rate=invoice.get("vat_rate", 21),
        vat_amount=invoice.get("vat_amount"),
        amount_total=invoice["amount_total"],
        currency=invoice.get("currency", "CZK"),
        payment_type=invoice.get("payment_type", "setup"),
        status=invoice["status"],
        description=invoice.get("description"),
        variable_symbol=invoice.get("variable_symbol"),
        rejected_reason=invoice.get("rejected_reason"),
        created_at=invoice.get("created_at"),
        updated_at=invoice.get("updated_at"),
        business_name=business_name,
    )


@router.post(
    "/projects/{project_id}/generate-invoice",
    response_model=InvoiceIssuedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_project_invoice(
    project_id: str,
    data: InvoiceIssuedCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Generate an invoice for a project."""
    supabase = get_supabase()

    # Verify access to project and get business_id
    project_result = (
        supabase.table("website_projects")
        .select("id, business_id, seller_id, domain, package, price_setup")
        .eq("id", project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    project = project_result.data
    business_id = project["business_id"]

    # Check access to business
    await get_business(business_id, current_user)

    # Get business name
    business_result = (
        supabase.table("businesses")
        .select("name")
        .eq("id", business_id)
        .single()
        .execute()
    )
    business_name = business_result.data.get("name") if business_result.data else None

    # Generate invoice number using database function
    # Format: YYYY-NNNN (e.g., 2025-0001)
    current_year = datetime.utcnow().year

    # Get the count of invoices this year to generate next number
    count_result = (
        supabase.table("invoices_issued")
        .select("id", count="exact")
        .like("invoice_number", f"{current_year}-%")
        .execute()
    )
    next_number = (count_result.count or 0) + 1
    invoice_number = f"{current_year}-{next_number:04d}"

    # Calculate dates
    issue_date = date.today()
    due_date = issue_date + timedelta(days=data.due_days)

    # Calculate VAT
    vat_amount = round(data.amount_without_vat * (data.vat_rate / 100), 2)
    amount_total = round(data.amount_without_vat + vat_amount, 2)

    # Create invoice
    insert_data = {
        "business_id": business_id,
        "project_id": project_id,
        "seller_id": project.get("seller_id") or current_user.id,
        "invoice_number": invoice_number,
        "issue_date": issue_date.isoformat(),
        "due_date": due_date.isoformat(),
        "amount_without_vat": data.amount_without_vat,
        "vat_rate": data.vat_rate,
        "vat_amount": vat_amount,
        "amount_total": amount_total,
        "currency": "CZK",
        "payment_type": data.payment_type.value,
        "status": "draft",
        "description": data.description,
        "variable_symbol": invoice_number.replace("-", ""),
    }

    result = supabase.table("invoices_issued").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit fakturu",
        )

    # Create follow-up activity for invoice
    activity_data = {
        "id": str(uuid4()),
        "business_id": business_id,
        "seller_id": current_user.id,
        "type": "note",
        "content": f"Faktura {invoice_number} vystavena - splatnost {due_date.strftime('%d.%m.%Y')}",
        "outcome": f"Částka: {amount_total:,.0f} Kč",
        "occurred_at": datetime.utcnow().isoformat(),
    }
    supabase.table("crm_activities").insert(activity_data).execute()

    # Update business follow-up date to invoice due date
    supabase.table("businesses").update(
        {
            "next_follow_up_at": due_date.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("id", business_id).execute()

    row = result.data[0]
    return InvoiceIssuedResponse(
        id=row["id"],
        business_id=row["business_id"],
        project_id=row.get("project_id"),
        seller_id=row.get("seller_id"),
        invoice_number=row["invoice_number"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        paid_date=row.get("paid_date"),
        amount_without_vat=row.get("amount_without_vat", 0),
        vat_rate=row.get("vat_rate", 21),
        vat_amount=row.get("vat_amount"),
        amount_total=row["amount_total"],
        currency=row.get("currency", "CZK"),
        payment_type=row.get("payment_type", "setup"),
        status=row["status"],
        description=row.get("description"),
        variable_symbol=row.get("variable_symbol"),
        rejected_reason=row.get("rejected_reason"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        business_name=business_name,
    )


@router.put(
    "/invoices-issued/{invoice_id}/status", response_model=InvoiceIssuedResponse
)
async def update_invoice_status(
    invoice_id: str,
    data: InvoiceStatusUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Update invoice status. When status changes to 'paid', automatically creates
    a commission entry in the seller's ledger.
    """
    supabase = get_supabase()

    # Get current invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data
    old_status = invoice["status"]
    new_status = data.status.value

    # Only admin can mark invoice as paid
    if new_status == "paid" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pouze administrátor může označit fakturu jako zaplacenou",
        )

    # Check access to business
    await get_business(invoice["business_id"], current_user)

    # Get business name for response
    business_result = (
        supabase.table("businesses")
        .select("name")
        .eq("id", invoice["business_id"])
        .single()
        .execute()
    )
    business_name = business_result.data.get("name") if business_result.data else None

    # Prepare update data
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow().isoformat(),
    }

    # If marking as paid, set paid_date
    if new_status == "paid":
        update_data["paid_date"] = data.paid_date or date.today().isoformat()

    # Update invoice
    result = (
        supabase.table("invoices_issued")
        .update(update_data)
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat fakturu",
        )

    # If status changed to 'paid', create commission entry
    if old_status != "paid" and new_status == "paid":
        seller_id = invoice.get("seller_id")

        if seller_id:
            # Get seller's commission rate
            seller_result = (
                supabase.table("sellers")
                .select("default_commission_rate")
                .eq("id", seller_id)
                .single()
                .execute()
            )

            commission_rate = 0.10  # Default 10%
            if seller_result.data and seller_result.data.get("default_commission_rate"):
                commission_rate = seller_result.data["default_commission_rate"] / 100

            # Calculate commission
            commission_amount = round(invoice["amount_total"] * commission_rate, 2)

            # Create ledger entry
            ledger_entry = {
                "seller_id": seller_id,
                "entry_type": "commission_earned",
                "amount": commission_amount,
                "related_invoice_id": invoice_id,
                "related_project_id": invoice.get("project_id"),
                "related_business_id": invoice["business_id"],
                "description": f"Provize za fakturu {invoice['invoice_number']} - {business_name}",
                "is_test": False,
                "created_by": current_user.id,
            }

            supabase.table("ledger_entries").insert(ledger_entry).execute()

    row = result.data[0]
    return InvoiceIssuedResponse(
        id=row["id"],
        business_id=row["business_id"],
        project_id=row.get("project_id"),
        seller_id=row.get("seller_id"),
        invoice_number=row["invoice_number"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        paid_date=row.get("paid_date"),
        amount_without_vat=row.get("amount_without_vat", 0),
        vat_rate=row.get("vat_rate", 21),
        vat_amount=row.get("vat_amount"),
        amount_total=row["amount_total"],
        currency=row.get("currency", "CZK"),
        payment_type=row.get("payment_type", "setup"),
        status=row["status"],
        description=row.get("description"),
        variable_symbol=row.get("variable_symbol"),
        rejected_reason=row.get("rejected_reason"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        business_name=business_name,
    )


# ============== Invoice Approval Workflow ==============


@router.put(
    "/invoices-issued/{invoice_id}/submit-for-approval",
    response_model=InvoiceIssuedResponse,
)
async def submit_invoice_for_approval(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Submit invoice for approval (draft -> pending_approval).
    Only sales can submit their own invoices.
    """
    supabase = get_supabase()

    # Get current invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*, businesses(name)")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data
    business_name = invoice.get("businesses", {}).get("name", "Unknown")

    # RBAC check - sales can only submit their own invoices
    if current_user.role == "sales" and invoice.get("seller_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáte oprávnění k této faktuře",
        )

    # Only draft invoices can be submitted
    if invoice["status"] != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nelze odeslat fakturu ve stavu '{invoice['status']}'. Pouze faktury ve stavu 'draft' mohou být odeslány ke schválení.",
        )

    # Update status
    update_data = {
        "status": "pending_approval",
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = (
        supabase.table("invoices_issued")
        .update(update_data)
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se odeslat fakturu ke schválení",
        )

    row = result.data[0]
    return InvoiceIssuedResponse(
        id=row["id"],
        business_id=row["business_id"],
        project_id=row.get("project_id"),
        seller_id=row.get("seller_id"),
        invoice_number=row["invoice_number"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        paid_date=row.get("paid_date"),
        amount_without_vat=row.get("amount_without_vat", 0),
        vat_rate=row.get("vat_rate", 21),
        vat_amount=row.get("vat_amount"),
        amount_total=row["amount_total"],
        currency=row.get("currency", "CZK"),
        payment_type=row.get("payment_type", "setup"),
        status=row["status"],
        description=row.get("description"),
        variable_symbol=row.get("variable_symbol"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        business_name=business_name,
    )


@router.get("/admin/invoices", response_model=AdminInvoiceListResponse)
async def get_admin_invoices(
    current_user: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(
        None, description="Filter by status (comma-separated)"
    ),
    seller_id: str | None = Query(None, description="Filter by seller"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Get list of all invoices for admin view.
    Supports filtering by status and seller.
    """
    supabase = get_supabase()

    # Base query
    query = supabase.table("invoices_issued").select(
        "*, businesses(name)", count="exact"
    )

    # Status filter
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",")]
        query = query.in_("status", statuses)

    # Seller filter
    if seller_id:
        query = query.eq("seller_id", seller_id)

    # Order by created_at desc
    query = query.order("created_at", desc=True)

    # Pagination
    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    # Get all seller IDs from results to fetch names
    seller_ids = list(
        set(row.get("seller_id") for row in result.data if row.get("seller_id"))
    )
    seller_names = {}
    if seller_ids:
        sellers_result = (
            supabase.table("sellers")
            .select("id, first_name, last_name")
            .in_("id", seller_ids)
            .execute()
        )
        for s in sellers_result.data or []:
            seller_names[s["id"]] = (
                f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()
            )

    # Transform response
    items = []
    for row in result.data:
        items.append(
            AdminInvoiceListItem(
                id=row["id"],
                invoice_number=row["invoice_number"],
                business_id=row["business_id"],
                business_name=row.get("businesses", {}).get("name"),
                seller_id=row.get("seller_id"),
                seller_name=seller_names.get(row.get("seller_id")),
                amount_total=row["amount_total"],
                status=row["status"],
                issue_date=row["issue_date"],
                due_date=row["due_date"],
                paid_date=row.get("paid_date"),
                payment_type=row.get("payment_type", "setup"),
                rejected_reason=row.get("rejected_reason"),
                created_at=row.get("created_at"),
            )
        )

    return AdminInvoiceListResponse(
        items=items, total=result.count or 0, page=page, limit=limit
    )


@router.put(
    "/invoices-issued/{invoice_id}/approve", response_model=InvoiceIssuedResponse
)
async def approve_invoice(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Approve an invoice (pending_approval -> issued).
    Only admin can approve invoices.
    """
    supabase = get_supabase()

    # Get current invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*, businesses(name)")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data
    business_name = invoice.get("businesses", {}).get("name", "Unknown")

    # Only pending_approval invoices can be approved
    if invoice["status"] != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nelze schválit fakturu ve stavu '{invoice['status']}'. Pouze faktury čekající na schválení mohou být schváleny.",
        )

    # Update status
    update_data = {
        "status": "issued",
        "updated_at": datetime.utcnow().isoformat(),
        "rejected_reason": None,  # Clear any previous rejection reason
    }

    result = (
        supabase.table("invoices_issued")
        .update(update_data)
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se schválit fakturu",
        )

    row = result.data[0]
    return InvoiceIssuedResponse(
        id=row["id"],
        business_id=row["business_id"],
        project_id=row.get("project_id"),
        seller_id=row.get("seller_id"),
        invoice_number=row["invoice_number"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        paid_date=row.get("paid_date"),
        amount_without_vat=row.get("amount_without_vat", 0),
        vat_rate=row.get("vat_rate", 21),
        vat_amount=row.get("vat_amount"),
        amount_total=row["amount_total"],
        currency=row.get("currency", "CZK"),
        payment_type=row.get("payment_type", "setup"),
        status=row["status"],
        description=row.get("description"),
        variable_symbol=row.get("variable_symbol"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        business_name=business_name,
    )


@router.put(
    "/invoices-issued/{invoice_id}/reject", response_model=InvoiceIssuedResponse
)
async def reject_invoice(
    invoice_id: str,
    data: InvoiceRejectRequest,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Reject an invoice with reason (pending_approval -> draft).
    Only admin can reject invoices.
    """
    supabase = get_supabase()

    # Get current invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*, businesses(name)")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data
    business_name = invoice.get("businesses", {}).get("name", "Unknown")

    # Only pending_approval invoices can be rejected
    if invoice["status"] != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nelze zamítnout fakturu ve stavu '{invoice['status']}'. Pouze faktury čekající na schválení mohou být zamítnuty.",
        )

    # Update status back to draft with rejection reason
    update_data = {
        "status": "draft",
        "rejected_reason": data.reason,
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = (
        supabase.table("invoices_issued")
        .update(update_data)
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se zamítnout fakturu",
        )

    row = result.data[0]
    return InvoiceIssuedResponse(
        id=row["id"],
        business_id=row["business_id"],
        project_id=row.get("project_id"),
        seller_id=row.get("seller_id"),
        invoice_number=row["invoice_number"],
        issue_date=row["issue_date"],
        due_date=row["due_date"],
        paid_date=row.get("paid_date"),
        amount_without_vat=row.get("amount_without_vat", 0),
        vat_rate=row.get("vat_rate", 21),
        vat_amount=row.get("vat_amount"),
        amount_total=row["amount_total"],
        currency=row.get("currency", "CZK"),
        payment_type=row.get("payment_type", "setup"),
        status=row["status"],
        description=row.get("description"),
        variable_symbol=row.get("variable_symbol"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        business_name=business_name,
    )


@router.get("/seller/claims", response_model=SellerClaimsResponse)
async def get_seller_claims(
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Get seller's commission claims summary.
    Returns total earned, already invoiced, and available to claim.
    """
    supabase = get_supabase()

    # Calculate total earned from ledger entries
    ledger_result = (
        supabase.table("ledger_entries")
        .select("amount")
        .eq("seller_id", current_user.id)
        .eq("entry_type", "commission_earned")
        .execute()
    )

    total_earned = 0
    if ledger_result.data:
        for entry in ledger_result.data:
            total_earned += entry.get("amount", 0)

    # Calculate already invoiced (approved + paid invoices from invoices_received)
    invoiced_result = (
        supabase.table("invoices_received")
        .select("amount_total")
        .eq("seller_id", current_user.id)
        .in_("status", ["approved", "paid"])
        .execute()
    )

    already_invoiced = 0
    if invoiced_result.data:
        for inv in invoiced_result.data:
            already_invoiced += inv.get("amount_total", 0)

    # Available to claim
    available_to_claim = total_earned - already_invoiced

    return SellerClaimsResponse(
        total_earned=total_earned,
        already_invoiced=already_invoiced,
        available_to_claim=max(0, available_to_claim),  # Can't be negative
    )


# ============== PDF Invoice Generation ==============


@router.post("/invoices-issued/{invoice_id}/generate-pdf")
async def generate_invoice_issued_pdf_endpoint(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Generate PDF for an issued invoice (Webomat -> Client).
    Uploads to Supabase Storage and updates pdf_path in database.
    Returns the public URL of the generated PDF.
    """
    from ..services.pdf import generate_invoice_issued_pdf, upload_pdf_to_storage

    supabase = get_supabase()

    # Get invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data

    # Check access to business
    await get_business(invoice["business_id"], current_user)

    # Get business data
    business_result = (
        supabase.table("businesses")
        .select("*")
        .eq("id", invoice["business_id"])
        .single()
        .execute()
    )

    if not business_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Firma nenalezena"
        )

    business = business_result.data

    # Get project data if exists
    project = None
    if invoice.get("project_id"):
        project_result = (
            supabase.table("website_projects")
            .select("*")
            .eq("id", invoice["project_id"])
            .single()
            .execute()
        )
        if project_result.data:
            project = project_result.data

    # Get platform billing info
    settings_result = (
        supabase.table("platform_settings")
        .select("value")
        .eq("key", "billing_info")
        .single()
        .execute()
    )

    platform_billing = {}
    if settings_result.data and settings_result.data.get("value"):
        platform_billing = settings_result.data["value"]

    # Generate PDF
    try:
        pdf_bytes = generate_invoice_issued_pdf(
            invoice=invoice,
            business=business,
            platform_billing=platform_billing,
            project=project,
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF knihovna není nainstalována: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při generování PDF: {str(e)}",
        )

    # Upload to storage
    year = (
        invoice["invoice_number"].split("-")[0]
        if "-" in invoice["invoice_number"]
        else str(date.today().year)
    )
    storage_path = f"invoices/issued/{year}/{invoice['invoice_number']}.pdf"

    pdf_url = await upload_pdf_to_storage(
        supabase_client=supabase,
        pdf_bytes=pdf_bytes,
        storage_path=storage_path,
    )

    if not pdf_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se nahrát PDF do úložiště",
        )

    # Update invoice with pdf_path
    supabase.table("invoices_issued").update(
        {
            "pdf_path": pdf_url,
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("id", invoice_id).execute()

    return {"pdf_url": pdf_url, "storage_path": storage_path}


@router.get("/invoices-issued/{invoice_id}/pdf")
async def download_invoice_issued_pdf(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Download PDF for an issued invoice.
    If PDF doesn't exist, generates it first.
    """
    from ..services.pdf import generate_invoice_issued_pdf

    supabase = get_supabase()

    # Get invoice
    invoice_result = (
        supabase.table("invoices_issued")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data

    # Check access to business
    await get_business(invoice["business_id"], current_user)

    # If PDF already exists, redirect to it
    if invoice.get("pdf_path"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=invoice["pdf_path"])

    # Generate PDF on-the-fly
    business_result = (
        supabase.table("businesses")
        .select("*")
        .eq("id", invoice["business_id"])
        .single()
        .execute()
    )

    if not business_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Firma nenalezena"
        )

    business = business_result.data

    project = None
    if invoice.get("project_id"):
        project_result = (
            supabase.table("website_projects")
            .select("*")
            .eq("id", invoice["project_id"])
            .single()
            .execute()
        )
        if project_result.data:
            project = project_result.data

    settings_result = (
        supabase.table("platform_settings")
        .select("value")
        .eq("key", "billing_info")
        .single()
        .execute()
    )

    platform_billing = {}
    if settings_result.data and settings_result.data.get("value"):
        platform_billing = settings_result.data["value"]

    try:
        pdf_bytes = generate_invoice_issued_pdf(
            invoice=invoice,
            business=business,
            platform_billing=platform_billing,
            project=project,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při generování PDF: {str(e)}",
        )

    filename = f"faktura-{invoice['invoice_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/invoices-received/{invoice_id}/generate-pdf")
async def generate_invoice_received_pdf_endpoint(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Generate PDF for a received invoice (Seller -> Webomat).
    Only the seller who owns the invoice or admin can generate it.
    """
    from ..services.pdf import generate_invoice_received_pdf, upload_pdf_to_storage

    supabase = get_supabase()

    # Get invoice
    invoice_result = (
        supabase.table("invoices_received")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data

    # Check access - only owner or admin
    if current_user.role != "admin" and invoice.get("seller_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáte oprávnění k této faktuře",
        )

    # Get seller data
    seller_result = (
        supabase.table("sellers")
        .select("*")
        .eq("id", invoice["seller_id"])
        .single()
        .execute()
    )

    if not seller_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obchodník nenalezen"
        )

    seller = seller_result.data

    # Get platform billing info
    settings_result = (
        supabase.table("platform_settings")
        .select("value")
        .eq("key", "billing_info")
        .single()
        .execute()
    )

    platform_billing = {}
    if settings_result.data and settings_result.data.get("value"):
        platform_billing = settings_result.data["value"]

    # Generate PDF
    try:
        pdf_bytes = generate_invoice_received_pdf(
            invoice=invoice,
            seller=seller,
            platform_billing=platform_billing,
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF knihovna není nainstalována: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při generování PDF: {str(e)}",
        )

    # Upload to storage
    storage_path = f"invoices/received/{seller['id']}/{invoice['invoice_number']}.pdf"

    pdf_url = await upload_pdf_to_storage(
        supabase_client=supabase,
        pdf_bytes=pdf_bytes,
        storage_path=storage_path,
    )

    if not pdf_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se nahrát PDF do úložiště",
        )

    # Update invoice with pdf_path
    supabase.table("invoices_received").update(
        {
            "pdf_path": pdf_url,
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("id", invoice_id).execute()

    return {"pdf_url": pdf_url, "storage_path": storage_path}


@router.get("/invoices-received/{invoice_id}/pdf")
async def download_invoice_received_pdf(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Download PDF for a received invoice.
    If PDF doesn't exist, generates it first.
    """
    from ..services.pdf import generate_invoice_received_pdf

    supabase = get_supabase()

    # Get invoice
    invoice_result = (
        supabase.table("invoices_received")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Faktura nenalezena"
        )

    invoice = invoice_result.data

    # Check access - only owner or admin
    if current_user.role != "admin" and invoice.get("seller_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáte oprávnění k této faktuře",
        )

    # If PDF already exists, redirect to it
    if invoice.get("pdf_path"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=invoice["pdf_path"])

    # Get seller data
    seller_result = (
        supabase.table("sellers")
        .select("*")
        .eq("id", invoice["seller_id"])
        .single()
        .execute()
    )

    if not seller_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Obchodník nenalezen"
        )

    seller = seller_result.data

    # Get platform billing info
    settings_result = (
        supabase.table("platform_settings")
        .select("value")
        .eq("key", "billing_info")
        .single()
        .execute()
    )

    platform_billing = {}
    if settings_result.data and settings_result.data.get("value"):
        platform_billing = settings_result.data["value"]

    try:
        pdf_bytes = generate_invoice_received_pdf(
            invoice=invoice,
            seller=seller,
            platform_billing=platform_billing,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při generování PDF: {str(e)}",
        )

    filename = f"faktura-{invoice['invoice_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
