from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_supabase
from ..dependencies import require_sales_or_admin
from ..schemas.auth import User
from ..schemas.website import GenerateWebsiteRequest, GenerateWebsiteResponse

router = APIRouter(prefix="/website", tags=["website generation"])


@router.post("/generate", response_model=GenerateWebsiteResponse)
async def generate_website(
    data: GenerateWebsiteRequest,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Generate website for a project.

    If dry_run=True, returns dummy HTML instead of calling Claude API.
    """
    supabase = get_supabase()

    # Verify project exists and user has access
    project_result = (
        supabase.table("website_projects")
        .select("id, business_id")
        .eq("id", data.project_id)
        .single()
        .execute()
    )

    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Projekt nenalezen"
        )

    project = project_result.data

    # Check access - sales can only work on projects where they are assigned or business owner
    if current_user.role == "sales":
        business_result = (
            supabase.table("businesses")
            .select("owner_seller_id")
            .eq("id", project["business_id"])
            .single()
            .execute()
        )

        if business_result.data:
            business_owner = business_result.data.get("owner_seller_id")
            if business_owner and business_owner != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Nemáte oprávnění k tomuto projektu",
                )

    # DRY RUN mode - return dummy HTML
    if data.dry_run:
        dummy_html = """<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dry Run Test Web</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        h1 {
            font-size: 3rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        p {
            font-size: 1.2rem;
            margin-bottom: 30px;
        }
        .badge {
            display: inline-block;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dry Run Test Web</h1>
        <p>Toto je testovací webová stránka generovaná v DRY RUN režimu.</p>
        <div class="badge">Webomat DRY RUN</div>
    </div>
</body>
</html>"""

        return GenerateWebsiteResponse(
            success=True,
            message="DRY RUN: Vygenerována testovací stránka",
            html_content=dummy_html,
        )

    # TODO: Implement actual Claude API call for production generation
    # For now, return error indicating this is not implemented yet
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Vlastní generování webu zatím není implementováno. Použijte DRY RUN režim.",
    )
