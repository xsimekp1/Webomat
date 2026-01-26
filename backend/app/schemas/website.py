from enum import Enum
from pydantic import BaseModel
from typing import Optional


class EnglishVersionMode(str, Enum):
    """Režim anglické verze webu."""
    no = "no"           # Pouze česká verze
    auto = "auto"       # Automatický překlad pomocí AI
    client = "client"   # Klient dodá anglické texty


class GenerateWebsiteRequest(BaseModel):
    project_id: str
    dry_run: bool = False  # DRY RUN mode flag
    include_english: EnglishVersionMode = EnglishVersionMode.no


class GenerateWebsiteResponse(BaseModel):
    success: bool
    message: str
    html_content: Optional[str] = None
    html_content_en: Optional[str] = None  # Anglická verze (pokud je)
    version_id: Optional[str] = None
    translation_status: Optional[str] = None  # pending/completed/client_required
