"""
Screenshot Service

Uses Playwright for capturing website screenshots.
Designed to run in background worker process.
"""

import asyncio
import io
import os
import uuid
from typing import Literal

# Playwright import is conditional - not required for API server
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from ..database import get_supabase


# Viewport configurations
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "mobile": {"width": 375, "height": 812},
    "thumbnail": {"width": 400, "height": 300},
}


async def capture_screenshot(
    url: str | None = None,
    html_content: str | None = None,
    viewport: Literal["desktop", "mobile", "thumbnail"] = "desktop",
) -> bytes:
    """
    Capture a screenshot of a URL or HTML content.

    Args:
        url: URL to capture (mutually exclusive with html_content)
        html_content: Raw HTML to render and capture
        viewport: Viewport size preset

    Returns:
        PNG image bytes
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        )

    if not url and not html_content:
        raise ValueError("Either url or html_content must be provided")

    vp = VIEWPORTS.get(viewport, VIEWPORTS["desktop"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        context = await browser.new_context(
            viewport=vp,
            device_scale_factor=2 if viewport == "thumbnail" else 1,
        )

        page = await context.new_page()

        try:
            if url:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            else:
                await page.set_content(html_content, wait_until="networkidle", timeout=30000)

            # Wait for any animations to settle
            await asyncio.sleep(0.5)

            # Capture screenshot
            screenshot = await page.screenshot(
                type="png",
                full_page=False if viewport == "thumbnail" else True,
            )

            return screenshot

        finally:
            await context.close()
            await browser.close()


async def upload_screenshot(
    image_bytes: bytes,
    filename: str,
    folder: str = "screenshots",
) -> str:
    """
    Upload screenshot to Supabase Storage.

    Args:
        image_bytes: PNG image bytes
        filename: Desired filename (without path)
        folder: Storage folder

    Returns:
        Public URL of uploaded image
    """
    supabase = get_supabase()

    # Generate unique path
    unique_filename = f"{folder}/{uuid.uuid4()}_{filename}"

    # Upload to storage
    result = supabase.storage.from_("webomat").upload(
        path=unique_filename,
        file=image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )

    if result.data is None:
        raise RuntimeError(f"Failed to upload screenshot: {result}")

    # Get public URL
    public_url = supabase.storage.from_("webomat").get_public_url(unique_filename)

    return public_url


async def capture_and_upload_version_screenshots(version_id: str) -> dict:
    """
    Capture all screenshots for a website version and update the database.

    Args:
        version_id: Website version ID

    Returns:
        Dict with screenshot URLs
    """
    supabase = get_supabase()

    # Get version data
    result = supabase.table("website_versions").select("*").eq("id", version_id).limit(1).execute()

    if not result.data:
        raise ValueError(f"Version {version_id} not found")

    version = result.data[0]
    url = version.get("public_url")
    html_content = version.get("html_content")

    if not url and not html_content:
        raise ValueError("Version has no URL or HTML content for screenshot")

    screenshots = {}

    # Capture desktop screenshot
    try:
        desktop_bytes = await capture_screenshot(
            url=url, html_content=html_content if not url else None, viewport="desktop"
        )
        screenshots["screenshot_desktop_url"] = await upload_screenshot(
            desktop_bytes, f"v{version['version_number']}_desktop.png", f"versions/{version_id}"
        )
    except Exception as e:
        print(f"Desktop screenshot failed: {e}")

    # Capture mobile screenshot
    try:
        mobile_bytes = await capture_screenshot(
            url=url, html_content=html_content if not url else None, viewport="mobile"
        )
        screenshots["screenshot_mobile_url"] = await upload_screenshot(
            mobile_bytes, f"v{version['version_number']}_mobile.png", f"versions/{version_id}"
        )
    except Exception as e:
        print(f"Mobile screenshot failed: {e}")

    # Capture thumbnail
    try:
        thumb_bytes = await capture_screenshot(
            url=url, html_content=html_content if not url else None, viewport="thumbnail"
        )
        screenshots["thumbnail_url"] = await upload_screenshot(
            thumb_bytes, f"v{version['version_number']}_thumb.png", f"versions/{version_id}"
        )
    except Exception as e:
        print(f"Thumbnail capture failed: {e}")

    # Update version with screenshot URLs
    if screenshots:
        supabase.table("website_versions").update(screenshots).eq("id", version_id).execute()

    return screenshots


def is_playwright_available() -> bool:
    """Check if Playwright is available for screenshot capture."""
    return PLAYWRIGHT_AVAILABLE
