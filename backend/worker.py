"""
Background Worker

Processes background jobs from the queue.
Run as a separate process on Railway.

Usage:
    python -m worker
    # or
    python worker.py
"""

import asyncio
import os
import sys
import signal
import uuid
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.jobs import (
    claim_next_job,
    complete_job,
    fail_job,
    get_job_handler,
    get_queue_stats,
)


# Worker configuration
POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "10"))  # seconds
WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
MAX_CONSECUTIVE_ERRORS = int(os.getenv("WORKER_MAX_ERRORS", "10"))

# Job types this worker handles
SUPPORTED_JOB_TYPES = [
    "screenshot_capture",
    "deploy_version",
    "undeploy_version",
    "cleanup_expired_links",
    "generate_thumbnail",
    "send_notification",
]

# Graceful shutdown flag
_shutdown_requested = False


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    global _shutdown_requested
    print(f"\n[{datetime.utcnow().isoformat()}] Shutdown signal received, finishing current job...")
    _shutdown_requested = True


async def process_job(job: dict) -> None:
    """
    Process a single job.

    Args:
        job: Job data from database
    """
    job_id = job["id"]
    job_type = job["job_type"]

    print(f"[{datetime.utcnow().isoformat()}] Processing job {job_id} ({job_type})")

    handler = get_job_handler(job_type)
    if not handler:
        await fail_job(job_id, f"No handler registered for job type: {job_type}")
        return

    try:
        result = await handler(job)
        await complete_job(job_id, result)
        print(f"[{datetime.utcnow().isoformat()}] Job {job_id} completed successfully")

    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        print(f"[{datetime.utcnow().isoformat()}] Job {job_id} failed: {error_message}")
        await fail_job(job_id, error_message)


async def worker_loop():
    """Main worker loop."""
    global _shutdown_requested

    print(f"[{datetime.utcnow().isoformat()}] Worker {WORKER_ID} starting")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Supported job types: {', '.join(SUPPORTED_JOB_TYPES)}")

    consecutive_errors = 0

    while not _shutdown_requested:
        try:
            # Claim next job
            job = await claim_next_job(
                job_types=SUPPORTED_JOB_TYPES,
                worker_id=WORKER_ID,
            )

            if job:
                consecutive_errors = 0
                await process_job(job)
            else:
                # No jobs available, wait before polling again
                await asyncio.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            _shutdown_requested = True

        except Exception as e:
            consecutive_errors += 1
            print(f"[{datetime.utcnow().isoformat()}] Worker error: {type(e).__name__}: {e}")

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                print(f"[{datetime.utcnow().isoformat()}] Too many consecutive errors, shutting down")
                break

            # Exponential backoff on errors
            wait_time = min(POLL_INTERVAL * (2 ** consecutive_errors), 300)
            await asyncio.sleep(wait_time)

    print(f"[{datetime.utcnow().isoformat()}] Worker {WORKER_ID} stopped")


async def print_stats():
    """Print queue statistics."""
    stats = await get_queue_stats()
    print("\nQueue Statistics:")
    print(f"  Total jobs: {stats['total']}")
    print(f"  By status: {stats['by_status']}")
    print(f"  By type: {stats['by_type']}")


def main():
    """Entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Check for required environment
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")
        sys.exit(1)

    # Check for optional services
    if not os.getenv("VERCEL_TOKEN") and not os.getenv("VERCEL_DEPLOY_TOKEN"):
        print("Warning: VERCEL_TOKEN not set - deployment jobs will fail")

    try:
        from app.services.screenshot import is_playwright_available
        if not is_playwright_available():
            print("Warning: Playwright not available - screenshot jobs will fail")
            print("  Install with: pip install playwright && playwright install chromium")
    except ImportError:
        print("Warning: Screenshot service not available")

    # Run worker
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
