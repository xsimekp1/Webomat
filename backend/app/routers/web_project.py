"""
Web Project Management Router

Endpoints for managing web projects, versions, deployments, screenshots, and share links.
"""

import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_supabase
from ..dependencies import require_sales_or_admin
from ..schemas.auth import User
from ..schemas.crm import (
    ProjectResponse,
    ProjectUpdate,
    WebsiteVersionCreate,
    WebsiteVersionUpdate,
    WebsiteVersionResponse,
    WebsiteVersionListResponse,
    VersionCommentResponse,
    VersionCommentUpdate,
    ShareLinkCreate,
    ShareLinkResponse,
    BackgroundJobResponse,
)

router = APIRouter(prefix="/web-project", tags=["Web Project"])


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


async def verify_project_access(supabase, project_id: str, current_user: User) -> dict:
    """Verify user has access to the project and return project data."""
    result = (
        supabase.table("website_projects")
        .select("*, businesses(id, owner_seller_id)")
        .eq("id", project_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    project = result.data[0]
    business = project.get("businesses", {})

    # RBAC check for sales
    if current_user.role == "sales":
        owner = business.get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Přístup odepřen"
            )

    return project


async def verify_version_access(supabase, version_id: str, current_user: User) -> dict:
    """Verify user has access to the version and return version data."""
    result = (
        supabase.table("website_versions")
        .select("*, website_projects(id, business_id, businesses(id, owner_seller_id))")
        .eq("id", version_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verze nenalezena"
        )

    version = result.data[0]
    project = version.get("website_projects", {})
    business = project.get("businesses", {})

    # RBAC check for sales
    if current_user.role == "sales":
        owner = business.get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Přístup odepřen"
            )

    return version


# ============================================
# Project Endpoints
# ============================================


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_web_project(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Get web project with full details."""
    supabase = get_supabase()
    project = await verify_project_access(supabase, project_id, current_user)

    return ProjectResponse(
        id=project["id"],
        business_id=project["business_id"],
        package=project.get("package", "start"),
        status=project.get("status", "offer"),
        price_setup=project.get("price_setup"),
        price_monthly=project.get("price_monthly"),
        domain=project.get("domain"),
        notes=project.get("notes"),
        required_deadline=project.get("required_deadline"),
        budget=project.get("budget"),
        domain_status=project.get("domain_status"),
        internal_notes=project.get("internal_notes"),
        client_notes=project.get("client_notes"),
        versions_count=project.get("versions_count"),
        latest_version_id=project.get("latest_version_id"),
        created_at=project.get("created_at"),
        updated_at=project.get("updated_at"),
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_web_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update web project details."""
    supabase = get_supabase()
    await verify_project_access(supabase, project_id, current_user)

    update_data = {}

    # Standard fields
    if data.package is not None:
        update_data["package"] = data.package.value if hasattr(data.package, "value") else data.package
    if data.status is not None:
        update_data["status"] = data.status.value if hasattr(data.status, "value") else data.status
    if data.price_setup is not None:
        update_data["price_setup"] = data.price_setup
    if data.price_monthly is not None:
        update_data["price_monthly"] = data.price_monthly
    if data.domain is not None:
        update_data["domain"] = data.domain
    if data.notes is not None:
        update_data["notes"] = data.notes

    # New fields
    if data.required_deadline is not None:
        update_data["required_deadline"] = data.required_deadline.isoformat() if data.required_deadline else None
    if data.budget is not None:
        update_data["budget"] = data.budget
    if data.domain_status is not None:
        update_data["domain_status"] = data.domain_status.value if hasattr(data.domain_status, "value") else data.domain_status
    if data.internal_notes is not None:
        update_data["internal_notes"] = data.internal_notes
    if data.client_notes is not None:
        update_data["client_notes"] = data.client_notes

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

    return await get_web_project(project_id, current_user)


# ============================================
# Version Endpoints
# ============================================


@router.get("/{project_id}/versions", response_model=WebsiteVersionListResponse)
async def list_versions(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """List all versions for a project, newest first."""
    supabase = get_supabase()
    await verify_project_access(supabase, project_id, current_user)

    result = (
        supabase.table("website_versions")
        .select("*")
        .eq("project_id", project_id)
        .neq("status", "archived")  # Exclude archived versions
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
                html_content=row.get("html_content"),
                html_content_en=row.get("html_content_en"),
                thumbnail_url=row.get("thumbnail_url"),
                screenshot_desktop_url=row.get("screenshot_desktop_url"),
                screenshot_mobile_url=row.get("screenshot_mobile_url"),
                public_url=row.get("public_url"),
                deployment_status=row.get("deployment_status", "none"),
                deployment_platform=row.get("deployment_platform"),
                deployment_id=row.get("deployment_id"),
                is_current=row.get("is_current", False),
                published_at=row.get("published_at"),
                parent_version_id=row.get("parent_version_id"),
                generation_instructions=row.get("generation_instructions"),
                created_at=row.get("created_at"),
                created_by=row.get("created_by"),
            )
        )

    return WebsiteVersionListResponse(items=versions, total=len(versions))


@router.post(
    "/{project_id}/versions",
    response_model=WebsiteVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    project_id: str,
    data: WebsiteVersionCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new version for a project."""
    supabase = get_supabase()
    await verify_project_access(supabase, project_id, current_user)

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
        "html_content": data.html_content,
        "html_content_en": data.html_content_en,
        "thumbnail_url": data.thumbnail_url,
        "parent_version_id": data.parent_version_id,
        "generation_instructions": data.generation_instructions,
        "created_by": current_user.id,
    }

    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

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
        notes=row.get("notes"),
        html_content=row.get("html_content"),
        html_content_en=row.get("html_content_en"),
        is_current=row.get("is_current", False),
        parent_version_id=row.get("parent_version_id"),
        generation_instructions=row.get("generation_instructions"),
        created_at=row.get("created_at"),
        created_by=row.get("created_by"),
    )


@router.put("/versions/{version_id}", response_model=WebsiteVersionResponse)
async def update_version(
    version_id: str,
    data: WebsiteVersionUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update a version."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    update_data = {}
    if data.status is not None:
        update_data["status"] = data.status.value if hasattr(data.status, "value") else data.status
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.html_content is not None:
        update_data["html_content"] = data.html_content
    if data.html_content_en is not None:
        update_data["html_content_en"] = data.html_content_en
    if data.is_current is not None:
        update_data["is_current"] = data.is_current
    if data.generation_instructions is not None:
        update_data["generation_instructions"] = data.generation_instructions

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Žádná data k aktualizaci"
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = (
        supabase.table("website_versions")
        .update(update_data)
        .eq("id", version_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat verzi",
        )

    row = result.data[0]
    return WebsiteVersionResponse(
        id=row["id"],
        project_id=row["project_id"],
        version_number=row["version_number"],
        status=row.get("status", "created"),
        notes=row.get("notes"),
        html_content=row.get("html_content"),
        html_content_en=row.get("html_content_en"),
        thumbnail_url=row.get("thumbnail_url"),
        screenshot_desktop_url=row.get("screenshot_desktop_url"),
        screenshot_mobile_url=row.get("screenshot_mobile_url"),
        public_url=row.get("public_url"),
        deployment_status=row.get("deployment_status", "none"),
        deployment_platform=row.get("deployment_platform"),
        deployment_id=row.get("deployment_id"),
        is_current=row.get("is_current", False),
        published_at=row.get("published_at"),
        parent_version_id=row.get("parent_version_id"),
        generation_instructions=row.get("generation_instructions"),
        created_at=row.get("created_at"),
        created_by=row.get("created_by"),
    )


@router.delete("/versions/{version_id}")
async def delete_version(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Soft delete a version (mark as archived)."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    # Check if version is currently deployed
    if version.get("deployment_status") == "deployed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nasazenou verzi nelze smazat. Nejdříve odeberte nasazení.",
        )

    # Check if version is marked as current
    if version.get("is_current"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuální verzi nelze smazat. Nejdříve nastavte jinou verzi jako aktuální.",
        )

    # Soft delete by marking as archived
    result = (
        supabase.table("website_versions")
        .update({
            "status": "archived",
        })
        .eq("id", version_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se smazat verzi",
        )

    return {"message": "Verze byla smazána"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Delete a web project (soft delete by marking as cancelled)."""
    supabase = get_supabase()
    project = await verify_project_access(supabase, project_id, current_user)

    # Check if any version is currently deployed
    versions_result = (
        supabase.table("website_versions")
        .select("id, deployment_status")
        .eq("project_id", project_id)
        .eq("deployment_status", "deployed")
        .limit(1)
        .execute()
    )

    if versions_result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Projekt nelze smazat, pokud má nasazené verze. Nejdříve odstraňte nasazení.",
        )

    # Soft delete by marking as cancelled
    result = (
        supabase.table("website_projects")
        .update({
            "status": "cancelled",
            "updated_at": datetime.utcnow().isoformat(),
        })
        .eq("id", project_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se smazat projekt",
        )

    # Also mark all versions as archived
    supabase.table("website_versions").update({
        "status": "archived"
    }).eq("project_id", project_id).execute()

    return {"message": "Projekt byl smazán"}


# ============================================
# Deployment Endpoints
# ============================================


@router.post("/versions/{version_id}/deploy")
async def deploy_version(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Queue a version for deployment to Vercel."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    # Check if version has HTML content
    if not version.get("html_content"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verze nemá HTML obsah k nasazení",
        )

    # Update deployment status
    supabase.table("website_versions").update({
        "deployment_status": "deploying",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", version_id).execute()

    # Create background job
    job_result = supabase.table("background_jobs").insert({
        "job_type": "deploy_version",
        "payload": {"version_id": version_id},
        "related_version_id": version_id,
        "related_project_id": version["project_id"],
    }).execute()

    return {
        "message": "Nasazení bylo zařazeno do fronty",
        "job_id": job_result.data[0]["id"] if job_result.data else None,
        "deployment_status": "deploying",
    }


@router.post("/versions/{version_id}/undeploy")
async def undeploy_version(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Remove deployment for a version."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    if version.get("deployment_status") != "deployed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verze není nasazena",
        )

    # Create background job for undeploy
    job_result = supabase.table("background_jobs").insert({
        "job_type": "undeploy_version",
        "payload": {
            "version_id": version_id,
            "deployment_id": version.get("deployment_id"),
        },
        "related_version_id": version_id,
        "related_project_id": version["project_id"],
    }).execute()

    # Update status
    supabase.table("website_versions").update({
        "deployment_status": "unpublished",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", version_id).execute()

    return {
        "message": "Odstranění nasazení bylo zařazeno do fronty",
        "job_id": job_result.data[0]["id"] if job_result.data else None,
    }


# ============================================
# Screenshot Endpoints
# ============================================


@router.post("/versions/{version_id}/screenshot")
async def capture_screenshot(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Queue screenshot capture for a version."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    # Check if version has public URL or HTML content
    if not version.get("public_url") and not version.get("html_content"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verze nemá URL ani HTML obsah pro screenshot",
        )

    # Create background job
    job_result = supabase.table("background_jobs").insert({
        "job_type": "screenshot_capture",
        "payload": {
            "version_id": version_id,
            "url": version.get("public_url"),
        },
        "related_version_id": version_id,
        "related_project_id": version["project_id"],
    }).execute()

    return {
        "message": "Screenshot byl zařazen do fronty",
        "job_id": job_result.data[0]["id"] if job_result.data else None,
    }


# ============================================
# Share Link Endpoints
# ============================================


@router.post("/versions/{version_id}/share-link", response_model=ShareLinkResponse)
async def create_share_link(
    version_id: str,
    data: ShareLinkCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a share link for client preview."""
    supabase = get_supabase()
    version = await verify_version_access(supabase, version_id, current_user)

    # Generate secure token
    token = secrets.token_urlsafe(48)  # 64 chars

    # Calculate expiration
    expires_at = None
    if data.expires_in_days:
        expires_at = (datetime.utcnow() + timedelta(days=data.expires_in_days)).isoformat()

    # Create share link
    result = supabase.table("preview_share_links").insert({
        "version_id": version_id,
        "token": token,
        "expires_at": expires_at,
        "max_views": data.max_views,
        "created_by": current_user.id,
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se vytvořit odkaz",
        )

    row = result.data[0]

    # Generate preview URL (using environment variable or default)
    import os
    frontend_url = os.getenv("FRONTEND_URL", "https://webomat.vercel.app")
    preview_url = f"{frontend_url}/preview/{token}"

    return ShareLinkResponse(
        id=row["id"],
        version_id=row["version_id"],
        token=row["token"],
        expires_at=row.get("expires_at"),
        view_count=row.get("view_count", 0),
        max_views=row.get("max_views"),
        is_active=row.get("is_active", True),
        created_at=row.get("created_at"),
        preview_url=preview_url,
    )


# ============================================
# Comments Endpoints
# ============================================


@router.get("/versions/{version_id}/comments", response_model=list[VersionCommentResponse])
async def list_version_comments(
    version_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
    status_filter: str | None = Query(None, description="Filter by status"),
):
    """List all comments for a version (internal view)."""
    supabase = get_supabase()
    await verify_version_access(supabase, version_id, current_user)

    query = (
        supabase.table("version_comments")
        .select("*")
        .eq("version_id", version_id)
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter)

    result = query.execute()

    comments = []
    for row in result.data or []:
        comments.append(
            VersionCommentResponse(
                id=row["id"],
                version_id=row["version_id"],
                author_type=row["author_type"],
                author_name=row.get("author_name"),
                author_email=row.get("author_email"),
                content=row["content"],
                anchor_type=row.get("anchor_type"),
                anchor_selector=row.get("anchor_selector"),
                anchor_x=row.get("anchor_x"),
                anchor_y=row.get("anchor_y"),
                status=row.get("status", "new"),
                resolved_by=row.get("resolved_by"),
                resolved_at=row.get("resolved_at"),
                resolution_note=row.get("resolution_note"),
                created_at=row.get("created_at"),
            )
        )

    return comments


@router.put("/comments/{comment_id}", response_model=VersionCommentResponse)
async def update_comment(
    comment_id: str,
    data: VersionCommentUpdate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Update comment status (acknowledge, resolve, reject)."""
    supabase = get_supabase()

    # Get comment and verify access
    comment_result = (
        supabase.table("version_comments")
        .select("*, website_versions(project_id, website_projects(business_id, businesses(owner_seller_id)))")
        .eq("id", comment_id)
        .limit(1)
        .execute()
    )

    if not comment_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Komentář nenalezen"
        )

    comment = comment_result.data[0]

    # Verify access through nested relations
    version = comment.get("website_versions", {})
    project = version.get("website_projects", {})
    business = project.get("businesses", {})

    if current_user.role == "sales":
        owner = business.get("owner_seller_id")
        if owner and owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Přístup odepřen"
            )

    update_data = {}
    if data.status is not None:
        update_data["status"] = data.status.value if hasattr(data.status, "value") else data.status
        if data.status in ["resolved", "rejected"]:
            update_data["resolved_by"] = current_user.id
            update_data["resolved_at"] = datetime.utcnow().isoformat()
    if data.resolution_note is not None:
        update_data["resolution_note"] = data.resolution_note

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Žádná data k aktualizaci"
        )

    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = (
        supabase.table("version_comments")
        .update(update_data)
        .eq("id", comment_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se aktualizovat komentář",
        )

    row = result.data[0]
    return VersionCommentResponse(
        id=row["id"],
        version_id=row["version_id"],
        author_type=row["author_type"],
        author_name=row.get("author_name"),
        author_email=row.get("author_email"),
        content=row["content"],
        anchor_type=row.get("anchor_type"),
        anchor_selector=row.get("anchor_selector"),
        anchor_x=row.get("anchor_x"),
        anchor_y=row.get("anchor_y"),
        status=row.get("status", "new"),
        resolved_by=row.get("resolved_by"),
        resolved_at=row.get("resolved_at"),
        resolution_note=row.get("resolution_note"),
        created_at=row.get("created_at"),
    )
