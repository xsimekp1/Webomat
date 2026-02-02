from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from enum import Enum

from ..database import get_supabase
from ..dependencies import require_sales_or_admin, require_admin
from ..schemas.auth import User
from ..schemas.website import GenerateWebsiteRequest, GenerateWebsiteResponse, EnglishVersionMode
from ..services.llm import process_translation_request, is_llm_available
from ..services.deployment import deploy_html_to_vercel, is_vercel_configured
from ..services.screenshot import capture_screenshot, upload_screenshot, is_playwright_available
from ..services.jobs import enqueue_job, get_job_status
from ..services.generator_tracking import create_run

router = APIRouter(prefix="/website", tags=["website generation"])


class GenerateTestRequest(BaseModel):
    """Request pro testovací generování webu (admin only)."""
    dry_run: bool = True  # Default je dry run
    business_name: str = "Test Firma s.r.o."
    business_type: str = "restaurace"
    include_english: EnglishVersionMode = EnglishVersionMode.no


class GenerateTestResponse(BaseModel):
    """Response pro testovací generování."""
    success: bool
    message: str
    html_content: str | None = None
    html_content_en: str | None = None
    translation_status: str | None = None  # pending/completed/client_required/unavailable
    strings_for_client: list[str] | None = None  # Texty k překladu klientem


class DeployTestRequest(BaseModel):
    """Request pro nasazení testovacího HTML na Vercel."""
    html_content: str
    business_name: str = "Test Preview"


class DeployTestResponse(BaseModel):
    """Response pro nasazení testovacího HTML."""
    success: bool
    message: str
    url: str | None = None
    deployment_id: str | None = None


class ScreenshotTestRequest(BaseModel):
    """Request pro screenshot testovacího HTML."""
    html_content: str
    viewport: str = "thumbnail"  # desktop, mobile, thumbnail


class ScreenshotTestResponse(BaseModel):
    """Response pro screenshot testovacího HTML."""
    success: bool
    message: str
    screenshot_url: str | None = None
    job_id: str | None = None  # Pokud se používá async worker


@router.get("/translation-status")
async def get_translation_status(
    current_user: Annotated[User, Depends(require_admin)],
):
    """Zkontroluje dostupnost překladové služby (OpenAI API)."""
    return {
        "available": is_llm_available(),
        "message": "OpenAI API je dostupné" if is_llm_available() else "OpenAI API klíč není nastaven"
    }


@router.get("/deployment-status")
async def get_deployment_status(
    current_user: Annotated[User, Depends(require_admin)],
):
    """Zkontroluje dostupnost Vercel deployment služby."""
    return {
        "available": is_vercel_configured(),
        "message": "Vercel deployment je dostupný" if is_vercel_configured() else "VERCEL_TOKEN není nastaven"
    }


@router.post("/deploy-test", response_model=DeployTestResponse)
async def deploy_test_website(
    data: DeployTestRequest,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Nasadit testovací HTML na Vercel.

    Vrací veřejnou URL, kterou lze sdílet s klientem.
    Admin only.
    """
    if not is_vercel_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vercel deployment není nakonfigurován (chybí VERCEL_TOKEN)",
        )

    if not data.html_content or len(data.html_content.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTML obsah je příliš krátký",
        )

    try:
        import uuid
        version_id = str(uuid.uuid4())[:8]

        result = await deploy_html_to_vercel(
            version_id=version_id,
            html_content=data.html_content,
            project_name=data.business_name,
        )

        return DeployTestResponse(
            success=True,
            message="Web byl úspěšně nasazen",
            url=result.get("url"),
            deployment_id=result.get("deployment_id"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nepodařilo se nasadit web: {str(e)}",
        )


@router.post("/screenshot-test", response_model=ScreenshotTestResponse)
async def screenshot_test_website(
    data: ScreenshotTestRequest,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """
    Pořídí screenshot z raw HTML obsahu.

    Pokud je Playwright dostupný na serveru, screenshot se pořídí okamžitě.
    Pokud ne, vytvoří se background job a vrátí job_id.

    Sales or Admin.
    """
    if not data.html_content or len(data.html_content.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTML obsah je příliš krátký",
        )

    # Validate viewport
    valid_viewports = ["desktop", "mobile", "thumbnail"]
    viewport = data.viewport if data.viewport in valid_viewports else "thumbnail"

    # Track screenshot run
    run = create_run(
        run_type="screenshot",
        seller_id=current_user.id,
        seller_email=current_user.email,
    )
    run.add_metadata("viewport", viewport)

    # Try direct capture if Playwright is available
    if is_playwright_available():
        try:
            import uuid

            # Capture screenshot from HTML
            screenshot_bytes = await capture_screenshot(
                html_content=data.html_content,
                viewport=viewport,
            )

            # Upload to Supabase Storage
            filename = f"test_{uuid.uuid4().hex[:8]}_{viewport}.png"
            screenshot_url = await upload_screenshot(
                image_bytes=screenshot_bytes,
                filename=filename,
                folder="test-screenshots",
            )

            # Track completed
            run.add_metadata("screenshot_url", screenshot_url)
            await run.save_completed()

            return ScreenshotTestResponse(
                success=True,
                message="Screenshot byl úspěšně pořízen",
                screenshot_url=screenshot_url,
            )

        except Exception as e:
            await run.save_failed(str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nepodařilo se pořídit screenshot: {str(e)}",
            )

    else:
        # Playwright not available on API server - try to queue job
        # This requires HTML to be accessible via URL, which we can do by:
        # 1. First deploy to Vercel, then screenshot
        # For now, return error with instructions
        await run.save_failed("Playwright není nainstalován na serveru")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Screenshot služba není dostupná. Playwright není nainstalován na serveru. "
                   "Pro pořízení screenshotu nejprve nasaďte web na Vercel.",
        )


@router.get("/screenshot-job/{job_id}")
async def get_screenshot_job_status(
    job_id: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Zkontroluje stav screenshot jobu.
    """
    job = await get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job nenalezen",
        )

    return {
        "job_id": job_id,
        "status": job.get("status"),
        "result": job.get("result"),
        "error_message": job.get("error_message"),
    }


@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test_website(
    data: GenerateTestRequest,
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Vygenerovat testovací webovou stránku (pouze admin).

    Nevyžaduje projekt - slouží pro testování generátoru.
    Pokud dry_run=True (default), vrátí dummy HTML.

    include_english:
    - "no": Pouze česká verze
    - "auto": Automatický překlad pomocí AI (vyžaduje OPENAI_API_KEY)
    - "client": Vrátí seznam textů k překladu klientem
    """
    # Track generator run
    run = create_run(
        run_type="dry_run" if data.dry_run else "claude_ai",
        seller_id=current_user.id,
        seller_email=current_user.email,
    )
    run.set_prompt_summary(f"Test: {data.business_name} ({data.business_type})")
    run.add_metadata("business_name", data.business_name)
    run.add_metadata("business_type", data.business_type)
    run.add_metadata("include_english", data.include_english.value)

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

        # Zpracování anglické verze
        html_content_en = None
        translation_status = None
        strings_for_client = None

        if data.include_english != EnglishVersionMode.no:
            translation_result = await process_translation_request(
                html_content=dummy_html,
                mode=data.include_english.value,
                business_type=data.business_type
            )

            if data.include_english == EnglishVersionMode.auto:
                if translation_result.success and translation_result.translated_content:
                    html_content_en = translation_result.translated_content
                    translation_status = "completed"
                elif not is_llm_available():
                    translation_status = "unavailable"
                else:
                    translation_status = "failed"

            elif data.include_english == EnglishVersionMode.client:
                strings_for_client = translation_result.strings_for_client
                translation_status = "client_required"

        # Track completed run
        await run.save_completed()

        return GenerateTestResponse(
            success=True,
            message=f"DRY RUN: Testovací stránka pro '{data.business_name}' ({data.business_type})",
            html_content=dummy_html,
            html_content_en=html_content_en,
            translation_status=translation_status,
            strings_for_client=strings_for_client,
        )

    # AI generování - zatím není implementováno
    await run.save_failed("AI generování zatím není implementováno")
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

    include_english:
    - "no": Czech version only
    - "auto": Auto-translate using AI (requires OPENAI_API_KEY)
    - "client": Returns list of strings for client to translate
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

    # Track generator run
    run = create_run(
        run_type="dry_run" if data.dry_run else "claude_ai",
        seller_id=current_user.id,
        seller_email=current_user.email,
        project_id=data.project_id,
        business_id=project["business_id"],
    )
    run.add_metadata("include_english", data.include_english.value)

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

        # Zpracování anglické verze
        html_content_en = None
        translation_status = None

        if data.include_english != EnglishVersionMode.no:
            translation_result = await process_translation_request(
                html_content=dummy_html,
                mode=data.include_english.value,
                business_type=None  # Mohli bychom načíst z businessu
            )

            if data.include_english == EnglishVersionMode.auto:
                if translation_result.success and translation_result.translated_content:
                    html_content_en = translation_result.translated_content
                    translation_status = "completed"
                elif not is_llm_available():
                    translation_status = "unavailable"
                else:
                    translation_status = "failed"

            elif data.include_english == EnglishVersionMode.client:
                translation_status = "client_required"

        # Track completed run
        await run.save_completed()

        return GenerateWebsiteResponse(
            success=True,
            message="DRY RUN: Vygenerována testovací stránka",
            html_content=dummy_html,
            html_content_en=html_content_en,
            translation_status=translation_status,
        )

    # TODO: Implement actual Claude API call for production generation
    # For now, return error indicating this is not implemented yet
    await run.save_failed("Vlastní generování webu zatím není implementováno")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Vlastní generování webu zatím není implementováno. Použijte DRY RUN režim.",
    )
