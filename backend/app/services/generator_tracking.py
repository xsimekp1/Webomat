"""
Service for tracking website generator runs.
Records all generator executions with cost and performance metrics.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..database import get_supabase


class GeneratorRun:
    """Helper class for tracking a single generator run."""

    def __init__(
        self,
        run_type: str,
        seller_id: Optional[str] = None,
        seller_email: Optional[str] = None,
        project_id: Optional[str] = None,
        business_id: Optional[str] = None,
    ):
        self.id = str(uuid4())
        self.run_type = run_type
        self.seller_id = seller_id
        self.seller_email = seller_email
        self.project_id = project_id
        self.business_id = business_id
        self.started_at = datetime.utcnow()
        self.version_id: Optional[str] = None
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cost_usd: float = 0.0
        self.model_used: Optional[str] = None
        self.prompt_summary: Optional[str] = None
        self.error_message: Optional[str] = None
        self.metadata: dict = {}
        self._saved = False

    def set_version(self, version_id: str):
        """Set the created version ID."""
        self.version_id = version_id

    def set_tokens(self, input_tokens: int, output_tokens: int, model: str):
        """Set token counts and model used."""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model_used = model
        self._calculate_cost()

    def set_cost(self, cost_usd: float):
        """Set cost manually (for external APIs)."""
        self.cost_usd = cost_usd

    def set_prompt_summary(self, summary: str):
        """Set a brief summary of the prompt."""
        self.prompt_summary = summary[:500] if summary else None  # Limit length

    def add_metadata(self, key: str, value):
        """Add metadata to the run."""
        self.metadata[key] = value

    def _calculate_cost(self):
        """Calculate cost based on model and tokens."""
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            # Claude models
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            # OpenAI models
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        }

        if self.model_used and self.model_used in pricing:
            rates = pricing[self.model_used]
            self.cost_usd = (
                (self.input_tokens * rates["input"] / 1_000_000) +
                (self.output_tokens * rates["output"] / 1_000_000)
            )

    async def save_started(self):
        """Save the run as started to database."""
        if self._saved:
            return

        supabase = get_supabase()

        data = {
            "id": self.id,
            "seller_id": self.seller_id,
            "seller_email": self.seller_email,
            "project_id": self.project_id,
            "business_id": self.business_id,
            "run_type": self.run_type,
            "status": "started",
            "started_at": self.started_at.isoformat(),
        }

        if self.prompt_summary:
            data["prompt_summary"] = self.prompt_summary

        if self.metadata:
            data["metadata"] = self.metadata

        try:
            supabase.table("generator_runs").insert(data).execute()
            self._saved = True
        except Exception as e:
            # Don't fail the main operation if tracking fails
            print(f"Warning: Failed to save generator run start: {e}")

    async def save_completed(self):
        """Update the run as completed."""
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        # Convert USD to CZK (approximate rate)
        cost_czk = round(self.cost_usd * 23.5, 2)  # ~23.5 CZK per USD

        supabase = get_supabase()

        update_data = {
            "status": "completed",
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "cost_usd": self.cost_usd,
            "cost_czk": cost_czk,
        }

        if self.version_id:
            update_data["version_id"] = self.version_id

        if self.model_used:
            update_data["model_used"] = self.model_used

        if self.metadata:
            update_data["metadata"] = self.metadata

        try:
            if self._saved:
                supabase.table("generator_runs").update(update_data).eq("id", self.id).execute()
            else:
                # Insert as completed if not saved yet
                update_data.update({
                    "id": self.id,
                    "seller_id": self.seller_id,
                    "seller_email": self.seller_email,
                    "project_id": self.project_id,
                    "business_id": self.business_id,
                    "run_type": self.run_type,
                    "started_at": self.started_at.isoformat(),
                })
                if self.prompt_summary:
                    update_data["prompt_summary"] = self.prompt_summary
                supabase.table("generator_runs").insert(update_data).execute()
        except Exception as e:
            print(f"Warning: Failed to save generator run completion: {e}")

    async def save_failed(self, error_message: str):
        """Update the run as failed."""
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        supabase = get_supabase()

        update_data = {
            "status": "failed",
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "error_message": error_message[:1000],  # Limit error length
        }

        try:
            if self._saved:
                supabase.table("generator_runs").update(update_data).eq("id", self.id).execute()
            else:
                update_data.update({
                    "id": self.id,
                    "seller_id": self.seller_id,
                    "seller_email": self.seller_email,
                    "project_id": self.project_id,
                    "business_id": self.business_id,
                    "run_type": self.run_type,
                    "started_at": self.started_at.isoformat(),
                })
                if self.prompt_summary:
                    update_data["prompt_summary"] = self.prompt_summary
                supabase.table("generator_runs").insert(update_data).execute()
        except Exception as e:
            print(f"Warning: Failed to save generator run failure: {e}")


def create_run(
    run_type: str,
    seller_id: Optional[str] = None,
    seller_email: Optional[str] = None,
    project_id: Optional[str] = None,
    business_id: Optional[str] = None,
) -> GeneratorRun:
    """
    Create a new generator run tracker.

    run_type values:
    - 'dry_run': Test run without AI (free)
    - 'claude_ai': Full AI generation with Claude
    - 'openai': Translation or other OpenAI tasks
    - 'screenshot': Screenshot capture
    """
    return GeneratorRun(
        run_type=run_type,
        seller_id=seller_id,
        seller_email=seller_email,
        project_id=project_id,
        business_id=business_id,
    )
