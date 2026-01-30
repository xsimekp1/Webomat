"""
Public Preview Router

Public endpoints for viewing website previews and submitting comments.
No authentication required - access controlled via share tokens.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ..database import get_supabase

router = APIRouter(prefix="/preview", tags=["Preview"])


# Rate limiting storage (in-memory, reset on restart)
# In production, use Redis
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 5  # max comments per IP per minute


def check_rate_limit(ip: str) -> bool:
    """Check if IP is rate limited. Returns True if allowed."""
    now = datetime.utcnow().timestamp()
    window_start = now - RATE_LIMIT_WINDOW

    if ip not in _rate_limit_store:
        _rate_limit_store[ip] = []

    # Clean old entries
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > window_start]

    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    _rate_limit_store[ip].append(now)
    return True


class PreviewInfo(BaseModel):
    """Public preview information."""
    version_id: str
    project_id: str
    version_number: int
    business_name: str | None = None
    domain: str | None = None
    has_html: bool = False


class PreviewCommentCreate(BaseModel):
    """Comment submission from preview page."""
    content: str
    author_name: str | None = None
    author_email: str | None = None
    # Anchor information
    anchor_type: str | None = None  # 'element', 'coordinates', 'general'
    anchor_selector: str | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None
    # Honeypot field for spam prevention
    website: str | None = None  # Should be empty - bots fill this


class PreviewCommentResponse(BaseModel):
    """Public comment view."""
    id: str
    content: str
    author_name: str | None = None
    anchor_type: str | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None
    created_at: datetime | None = None


async def get_share_link(token: str) -> dict:
    """Validate share link token and return link data."""
    supabase = get_supabase()

    result = (
        supabase.table("preview_share_links")
        .select("*, website_versions(*, website_projects(*, businesses(name)))")
        .eq("token", token)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odkaz nenalezen nebo vypršel",
        )

    link = result.data[0]

    # Check expiration
    if link.get("expires_at"):
        expires = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.utcnow().replace(tzinfo=expires.tzinfo):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Platnost odkazu vypršela",
            )

    # Check max views
    if link.get("max_views") and link.get("view_count", 0) >= link["max_views"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Odkaz dosáhl maximálního počtu zobrazení",
        )

    return link


@router.get("/{token}", response_model=PreviewInfo)
async def get_preview_info(token: str):
    """Get preview information (public)."""
    link = await get_share_link(token)
    supabase = get_supabase()

    version = link.get("website_versions", {})
    project = version.get("website_projects", {})
    business = project.get("businesses", {})

    # Increment view count
    supabase.table("preview_share_links").update({
        "view_count": (link.get("view_count") or 0) + 1,
        "last_viewed_at": datetime.utcnow().isoformat(),
    }).eq("id", link["id"]).execute()

    return PreviewInfo(
        version_id=version["id"],
        project_id=version["project_id"],
        version_number=version["version_number"],
        business_name=business.get("name"),
        domain=project.get("domain"),
        has_html=bool(version.get("html_content")),
    )


@router.get("/{token}/html")
async def get_preview_html(token: str):
    """Get HTML content for preview (public)."""
    link = await get_share_link(token)

    version = link.get("website_versions", {})
    html_content = version.get("html_content")

    if not html_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HTML obsah není k dispozici",
        )

    return {
        "html_content": html_content,
        "html_content_en": version.get("html_content_en"),
        "version_number": version["version_number"],
    }


@router.post("/{token}/comments", response_model=PreviewCommentResponse)
async def add_preview_comment(
    token: str,
    data: PreviewCommentCreate,
    request: Request,
):
    """Add a comment to the preview (public, rate limited)."""
    # Check honeypot
    if data.website:  # Bot filled this field
        # Return success but don't save (silent rejection)
        return PreviewCommentResponse(
            id="fake-id",
            content=data.content,
            author_name=data.author_name,
            created_at=datetime.utcnow(),
        )

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Příliš mnoho požadavků. Zkuste to později.",
        )

    link = await get_share_link(token)
    supabase = get_supabase()

    version = link.get("website_versions", {})

    # Validate content
    if not data.content or len(data.content.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Komentář musí mít alespoň 3 znaky",
        )

    if len(data.content) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Komentář je příliš dlouhý (max 5000 znaků)",
        )

    # Create comment
    result = supabase.table("version_comments").insert({
        "version_id": version["id"],
        "author_type": "client",
        "author_name": data.author_name,
        "author_email": data.author_email,
        "access_token": token,
        "content": data.content.strip(),
        "anchor_type": data.anchor_type,
        "anchor_selector": data.anchor_selector,
        "anchor_x": data.anchor_x,
        "anchor_y": data.anchor_y,
        "status": "new",
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nepodařilo se uložit komentář",
        )

    row = result.data[0]
    return PreviewCommentResponse(
        id=row["id"],
        content=row["content"],
        author_name=row.get("author_name"),
        anchor_type=row.get("anchor_type"),
        anchor_x=row.get("anchor_x"),
        anchor_y=row.get("anchor_y"),
        created_at=row.get("created_at"),
    )


@router.get("/{token}/comments", response_model=list[PreviewCommentResponse])
async def list_preview_comments(token: str):
    """List comments for a preview (public, client comments only)."""
    link = await get_share_link(token)
    supabase = get_supabase()

    version = link.get("website_versions", {})

    result = (
        supabase.table("version_comments")
        .select("id, content, author_name, anchor_type, anchor_x, anchor_y, created_at")
        .eq("version_id", version["id"])
        .eq("author_type", "client")  # Only show client comments
        .order("created_at", desc=False)
        .execute()
    )

    comments = []
    for row in result.data or []:
        comments.append(
            PreviewCommentResponse(
                id=row["id"],
                content=row["content"],
                author_name=row.get("author_name"),
                anchor_type=row.get("anchor_type"),
                anchor_x=row.get("anchor_x"),
                anchor_y=row.get("anchor_y"),
                created_at=row.get("created_at"),
            )
        )

    return comments
