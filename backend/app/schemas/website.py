from pydantic import BaseModel
from typing import Optional


class GenerateWebsiteRequest(BaseModel):
    project_id: str
    dry_run: bool = False  # DRY RUN mode flag


class GenerateWebsiteResponse(BaseModel):
    success: bool
    message: str
    html_content: Optional[str] = None
    version_id: Optional[str] = None
