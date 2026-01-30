"""
Deployment Service

Handles deployment of website versions to Vercel.
"""

import os
import json
import httpx
from datetime import datetime

from ..database import get_supabase


VERCEL_API_URL = "https://api.vercel.com"


def get_vercel_token() -> str:
    """Get Vercel API token from environment."""
    token = os.getenv("VERCEL_DEPLOY_TOKEN") or os.getenv("VERCEL_TOKEN")
    if not token:
        raise RuntimeError("VERCEL_DEPLOY_TOKEN environment variable not set")
    return token


async def deploy_html_to_vercel(
    version_id: str,
    html_content: str,
    project_name: str | None = None,
) -> dict:
    """
    Deploy HTML content to Vercel as a static site.

    Args:
        version_id: Website version ID (used for naming)
        html_content: HTML content to deploy
        project_name: Optional project name prefix

    Returns:
        Dict with deployment info (url, id, etc.)
    """
    token = get_vercel_token()

    # Create deployment name
    name = f"webomat-preview-{version_id[:8]}"
    if project_name:
        name = f"webomat-{project_name.lower().replace(' ', '-')[:20]}-{version_id[:8]}"

    # Prepare files for deployment
    # Vercel expects files in a specific format
    files = [
        {
            "file": "index.html",
            "data": html_content,
        },
    ]

    # Create deployment via Vercel API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VERCEL_API_URL}/v13/deployments",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "name": name,
                "files": files,
                "target": "production",
                "projectSettings": {
                    "framework": None,  # Static HTML
                },
            },
            timeout=60.0,
        )

        if response.status_code not in (200, 201):
            error_detail = response.text
            raise RuntimeError(f"Vercel deployment failed: {response.status_code} - {error_detail}")

        result = response.json()

        return {
            "deployment_id": result.get("id"),
            "url": f"https://{result.get('url')}",
            "ready_state": result.get("readyState"),
            "created_at": result.get("createdAt"),
        }


async def get_deployment_status(deployment_id: str) -> dict:
    """
    Get status of a Vercel deployment.

    Args:
        deployment_id: Vercel deployment ID

    Returns:
        Dict with deployment status
    """
    token = get_vercel_token()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VERCEL_API_URL}/v13/deployments/{deployment_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=30.0,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Failed to get deployment status: {response.status_code}")

        result = response.json()

        return {
            "deployment_id": result.get("id"),
            "url": result.get("url"),
            "ready_state": result.get("readyState"),
            "state": result.get("state"),
        }


async def delete_deployment(deployment_id: str) -> bool:
    """
    Delete a Vercel deployment.

    Args:
        deployment_id: Vercel deployment ID

    Returns:
        True if deleted successfully
    """
    token = get_vercel_token()

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{VERCEL_API_URL}/v13/deployments/{deployment_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=30.0,
        )

        # 200 or 204 = success, 404 = already deleted
        return response.status_code in (200, 204, 404)


async def deploy_version(version_id: str) -> dict:
    """
    Deploy a website version to Vercel.

    Args:
        version_id: Website version ID

    Returns:
        Dict with deployment result
    """
    supabase = get_supabase()

    # Get version data
    result = supabase.table("website_versions").select(
        "*, website_projects(domain, businesses(name))"
    ).eq("id", version_id).limit(1).execute()

    if not result.data:
        raise ValueError(f"Version {version_id} not found")

    version = result.data[0]
    html_content = version.get("html_content")

    if not html_content:
        raise ValueError("Version has no HTML content to deploy")

    # Get project name from business
    project = version.get("website_projects", {})
    business = project.get("businesses", {})
    project_name = business.get("name") or project.get("domain")

    # Deploy to Vercel
    deployment = await deploy_html_to_vercel(
        version_id=version_id,
        html_content=html_content,
        project_name=project_name,
    )

    # Update version with deployment info
    supabase.table("website_versions").update({
        "public_url": deployment["url"],
        "deployment_id": deployment["deployment_id"],
        "deployment_platform": "vercel",
        "deployment_status": "deployed",
        "published_at": datetime.utcnow().isoformat(),
    }).eq("id", version_id).execute()

    return deployment


async def undeploy_version(version_id: str) -> bool:
    """
    Remove deployment for a website version.

    Args:
        version_id: Website version ID

    Returns:
        True if undeployed successfully
    """
    supabase = get_supabase()

    # Get version data
    result = supabase.table("website_versions").select(
        "deployment_id, deployment_status"
    ).eq("id", version_id).limit(1).execute()

    if not result.data:
        raise ValueError(f"Version {version_id} not found")

    version = result.data[0]
    deployment_id = version.get("deployment_id")

    if deployment_id:
        # Delete from Vercel
        await delete_deployment(deployment_id)

    # Update version status
    supabase.table("website_versions").update({
        "deployment_status": "unpublished",
        "public_url": None,
    }).eq("id", version_id).execute()

    return True


def is_vercel_configured() -> bool:
    """Check if Vercel deployment is configured."""
    return bool(os.getenv("VERCEL_DEPLOY_TOKEN") or os.getenv("VERCEL_TOKEN"))
