from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from ..database import get_supabase
from ..dependencies import get_current_active_user
from ..schemas.auth import User

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image(file: UploadFile) -> str:
    """Validate uploaded image and return extension."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soubor nemá název"
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nepodporovaný formát. Povolené: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return ext


@router.post("/avatar")
async def upload_avatar(
    file: Annotated[UploadFile, File(description="Avatar image file")],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Upload avatar image for current user.

    Accepts: PNG, JPG, JPEG, GIF, WEBP (max 5MB)
    Returns: URL of uploaded avatar
    """
    ext = validate_image(file)

    # Read file content
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Soubor je příliš velký (max 5 MB)"
        )

    supabase = get_supabase()

    # Generate unique filename
    filename = f"{current_user.id}/{uuid.uuid4().hex}.{ext}"

    try:
        # Upload to Supabase Storage
        result = supabase.storage.from_("avatars").upload(
            path=filename,
            file=content,
            file_options={"content-type": file.content_type or f"image/{ext}"}
        )

        # Get public URL
        public_url = supabase.storage.from_("avatars").get_public_url(filename)

        # Update user's avatar_url in database
        supabase.table("sellers").update({
            "avatar_url": public_url
        }).eq("id", current_user.id).execute()

        return {
            "message": "Avatar úspěšně nahrán",
            "avatar_url": public_url
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chyba při nahrávání: {str(e)}"
        )


@router.delete("/avatar")
async def delete_avatar(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete current user's avatar."""
    supabase = get_supabase()

    # Get current avatar URL
    result = supabase.table("sellers").select("avatar_url").eq(
        "id", current_user.id
    ).single().execute()

    if result.data and result.data.get("avatar_url"):
        try:
            # Extract path from URL (after /avatars/)
            url = result.data["avatar_url"]
            if "/avatars/" in url:
                path = url.split("/avatars/")[-1].split("?")[0]
                supabase.storage.from_("avatars").remove([path])
        except Exception:
            pass  # Ignore storage deletion errors

    # Clear avatar_url in database
    supabase.table("sellers").update({
        "avatar_url": None
    }).eq("id", current_user.id).execute()

    return {"message": "Avatar smazán"}
