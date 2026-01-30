"""
Background Jobs Service

Simple DB-polling job queue for async tasks.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Callable, Any

from ..database import get_supabase


# Job handlers registry
_job_handlers: dict[str, Callable] = {}


def register_job_handler(job_type: str):
    """Decorator to register a job handler function."""
    def decorator(func: Callable):
        _job_handlers[job_type] = func
        return func
    return decorator


def get_job_handler(job_type: str) -> Callable | None:
    """Get handler function for a job type."""
    return _job_handlers.get(job_type)


async def enqueue_job(
    job_type: str,
    payload: dict | None = None,
    priority: int = 0,
    scheduled_for: datetime | None = None,
    related_version_id: str | None = None,
    related_project_id: str | None = None,
) -> str:
    """
    Add a new job to the queue.

    Args:
        job_type: Type of job (must match registered handler)
        payload: Job-specific data
        priority: Higher = more urgent (default 0)
        scheduled_for: When to run (default now)
        related_version_id: Optional related version
        related_project_id: Optional related project

    Returns:
        Job ID
    """
    supabase = get_supabase()

    result = supabase.table("background_jobs").insert({
        "job_type": job_type,
        "payload": payload or {},
        "priority": priority,
        "scheduled_for": (scheduled_for or datetime.utcnow()).isoformat(),
        "related_version_id": related_version_id,
        "related_project_id": related_project_id,
        "status": "pending",
    }).execute()

    if not result.data:
        raise RuntimeError("Failed to enqueue job")

    return result.data[0]["id"]


async def claim_next_job(
    job_types: list[str],
    worker_id: str,
    lock_duration_minutes: int = 5,
) -> dict | None:
    """
    Claim the next available job for processing.

    Args:
        job_types: List of job types this worker can handle
        worker_id: Unique identifier for this worker
        lock_duration_minutes: How long to lock the job

    Returns:
        Job data or None if no jobs available
    """
    supabase = get_supabase()
    now = datetime.utcnow()

    # Find next pending job
    result = supabase.table("background_jobs").select("*").eq(
        "status", "pending"
    ).in_(
        "job_type", job_types
    ).lte(
        "scheduled_for", now.isoformat()
    ).or_(
        f"locked_until.is.null,locked_until.lt.{now.isoformat()}"
    ).order(
        "priority", desc=True
    ).order(
        "scheduled_for"
    ).limit(1).execute()

    if not result.data:
        return None

    job = result.data[0]

    # Check attempts
    if job.get("attempts", 0) >= job.get("max_attempts", 3):
        return None

    # Try to claim the job (optimistic locking)
    lock_until = (now + timedelta(minutes=lock_duration_minutes)).isoformat()

    update_result = supabase.table("background_jobs").update({
        "status": "processing",
        "worker_id": worker_id,
        "locked_until": lock_until,
        "started_at": now.isoformat() if not job.get("started_at") else job["started_at"],
        "attempts": (job.get("attempts") or 0) + 1,
    }).eq(
        "id", job["id"]
    ).eq(
        "status", "pending"  # Ensure still pending (optimistic lock)
    ).execute()

    if not update_result.data:
        # Another worker claimed it
        return None

    return update_result.data[0]


async def complete_job(job_id: str, result: dict | None = None) -> None:
    """
    Mark a job as successfully completed.

    Args:
        job_id: Job ID
        result: Optional result data
    """
    supabase = get_supabase()

    supabase.table("background_jobs").update({
        "status": "completed",
        "result": result,
        "completed_at": datetime.utcnow().isoformat(),
        "locked_until": None,
    }).eq("id", job_id).execute()


async def fail_job(job_id: str, error_message: str) -> None:
    """
    Mark a job as failed.

    If attempts < max_attempts, job will be retried with exponential backoff.

    Args:
        job_id: Job ID
        error_message: Error description
    """
    supabase = get_supabase()

    # Get current job state
    result = supabase.table("background_jobs").select(
        "attempts, max_attempts"
    ).eq("id", job_id).limit(1).execute()

    if not result.data:
        return

    job = result.data[0]
    attempts = job.get("attempts", 1)
    max_attempts = job.get("max_attempts", 3)

    if attempts >= max_attempts:
        # Permanently failed
        supabase.table("background_jobs").update({
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat(),
            "locked_until": None,
        }).eq("id", job_id).execute()
    else:
        # Schedule retry with exponential backoff
        retry_at = datetime.utcnow() + timedelta(minutes=2 ** attempts)
        supabase.table("background_jobs").update({
            "status": "pending",
            "error_message": error_message,
            "scheduled_for": retry_at.isoformat(),
            "locked_until": None,
        }).eq("id", job_id).execute()


async def get_job_status(job_id: str) -> dict | None:
    """
    Get current status of a job.

    Args:
        job_id: Job ID

    Returns:
        Job data or None
    """
    supabase = get_supabase()

    result = supabase.table("background_jobs").select("*").eq(
        "id", job_id
    ).limit(1).execute()

    return result.data[0] if result.data else None


async def cancel_job(job_id: str) -> bool:
    """
    Cancel a pending job.

    Args:
        job_id: Job ID

    Returns:
        True if cancelled, False if job was already processing/completed
    """
    supabase = get_supabase()

    result = supabase.table("background_jobs").update({
        "status": "cancelled",
    }).eq(
        "id", job_id
    ).eq(
        "status", "pending"
    ).execute()

    return bool(result.data)


async def cleanup_old_jobs(days: int = 30) -> int:
    """
    Delete completed/failed jobs older than specified days.

    Args:
        days: Delete jobs older than this many days

    Returns:
        Number of deleted jobs
    """
    supabase = get_supabase()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    result = supabase.table("background_jobs").delete().in_(
        "status", ["completed", "failed", "cancelled"]
    ).lt(
        "created_at", cutoff
    ).execute()

    return len(result.data) if result.data else 0


async def get_queue_stats() -> dict:
    """
    Get job queue statistics.

    Returns:
        Dict with queue statistics
    """
    supabase = get_supabase()

    result = supabase.table("background_jobs").select("status, job_type").execute()

    stats = {
        "total": 0,
        "by_status": {},
        "by_type": {},
    }

    for job in result.data or []:
        stats["total"] += 1

        status = job.get("status", "unknown")
        job_type = job.get("job_type", "unknown")

        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        stats["by_type"][job_type] = stats["by_type"].get(job_type, 0) + 1

    return stats


# ============================================
# Job Handlers
# ============================================


@register_job_handler("screenshot_capture")
async def handle_screenshot_capture(job: dict) -> dict:
    """Handle screenshot capture job."""
    from .screenshot import capture_and_upload_version_screenshots

    payload = job.get("payload", {})
    version_id = payload.get("version_id")

    if not version_id:
        raise ValueError("version_id is required in payload")

    screenshots = await capture_and_upload_version_screenshots(version_id)
    return {"screenshots": screenshots}


@register_job_handler("deploy_version")
async def handle_deploy_version(job: dict) -> dict:
    """Handle version deployment job."""
    from .deployment import deploy_version

    payload = job.get("payload", {})
    version_id = payload.get("version_id")

    if not version_id:
        raise ValueError("version_id is required in payload")

    deployment = await deploy_version(version_id)
    return {"deployment": deployment}


@register_job_handler("undeploy_version")
async def handle_undeploy_version(job: dict) -> dict:
    """Handle version undeployment job."""
    from .deployment import undeploy_version

    payload = job.get("payload", {})
    version_id = payload.get("version_id")

    if not version_id:
        raise ValueError("version_id is required in payload")

    success = await undeploy_version(version_id)
    return {"success": success}


@register_job_handler("cleanup_expired_links")
async def handle_cleanup_expired_links(job: dict) -> dict:
    """Clean up expired share links."""
    supabase = get_supabase()
    now = datetime.utcnow().isoformat()

    # Deactivate expired links
    result = supabase.table("preview_share_links").update({
        "is_active": False,
    }).lt(
        "expires_at", now
    ).eq(
        "is_active", True
    ).execute()

    return {"deactivated_count": len(result.data) if result.data else 0}
