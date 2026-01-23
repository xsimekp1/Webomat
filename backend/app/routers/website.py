from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..database import get_supabase
from ..dependencies import require_sales_or_admin, require_admin
from ..schemas.auth import User
from ..schemas.website import GenerateWebsiteRequest, GenerateWebsiteResponse

router = APIRouter(prefix="/website", tags=["website generation"])


class GenerateTestRequest(BaseModel):
    """Request pro testovací generování webu (admin only)."""
    dry_run: bool = True  # Default je dry run
    business_name: str = "Test Firma s.r.o."
    business_type: str = "restaurace"


class GenerateTestResponse(BaseModel):
    """Response pro testovací generování."""
    success: bool
    message: str
    html_content: str | None = None


@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test_website(
    data: GenerateTestRequest,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Vygenerovat testovací webovou stránku (pouze admin).

    Nevyžaduje projekt - slouží pro testování generátoru.
    Pokud dry_run=True (default), vrátí dummy HTML.
    """

    if data.dry_run:
        # Dry run - vrátíme pěknou testovací stránku
        dummy_html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.business_name} - Testovací web</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 100px 20px;
            text-align: center;
        }}
        .hero h1 {{
            font-size: 3rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .hero p {{
            font-size: 1.3rem;
            opacity: 0.9;
        }}
        .badge {{
            display: inline-block;
            margin-top: 30px;
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 30px;
            font-weight: bold;
            border: 2px solid rgba(255,255,255,0.3);
        }}
        .content {{
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 20px;
        }}
        .content h2 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        .services {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .service-card {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
        }}
        .service-card .icon {{
            font-size: 2.5rem;
            margin-bottom: 15px;
        }}
        .footer {{
            background: #1a1a2e;
            color: white;
            text-align: center;
            padding: 40px 20px;
        }}
        .footer .test-info {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <section class="hero">
        <h1>{data.business_name}</h1>
        <p>Kategorie: {data.business_type}</p>
        <div class="badge">🧪 DRY RUN TEST</div>
    </section>

    <section class="content">
        <h2>O nás</h2>
        <p>Toto je testovací webová stránka vygenerovaná v DRY RUN režimu.
           Slouží pro ověření funkčnosti generátoru webů bez nutnosti volat AI API.</p>

        <div class="services">
            <div class="service-card">
                <div class="icon">⚡</div>
                <h3>Rychlé</h3>
                <p>Generování bez API</p>
            </div>
            <div class="service-card">
                <div class="icon">💰</div>
                <h3>Zdarma</h3>
                <p>Žádné náklady</p>
            </div>
            <div class="service-card">
                <div class="icon">🔧</div>
                <h3>Testování</h3>
                <p>Pro vývojáře</p>
            </div>
        </div>
    </section>

    <footer class="footer">
        <p>&copy; 2024 {data.business_name}</p>
        <div class="test-info">
            Webomat DRY RUN | Vygenerováno: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC
        </div>
    </footer>
</body>
</html>"""

        return GenerateTestResponse(
            success=True,
            message=f"DRY RUN: Testovací stránka pro '{data.business_name}' ({data.business_type})",
            html_content=dummy_html,
        )

    # AI generování - zatím není implementováno
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI generování zatím není implementováno. Použijte dry_run=true.",
    )


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
