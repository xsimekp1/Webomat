from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class CRMStatus(str, Enum):
    new = "new"
    calling = "calling"
    interested = "interested"
    offer_sent = "offer_sent"
    won = "won"
    lost = "lost"
    dnc = "dnc"


class ActivityType(str, Enum):
    call = "call"
    email = "email"
    meeting = "meeting"
    note = "note"
    message = "message"


# Business schemas
class BusinessBase(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    category: str | None = None
    notes: str | None = None
    # Fakturační údaje
    ico: str | None = None
    dic: str | None = None
    billing_address: str | None = None
    bank_account: str | None = None
    contact_person: str | None = None
    # Logo firmy
    logo_url: str | None = None


class BusinessCreate(BusinessBase):
    status_crm: CRMStatus = CRMStatus.new
    owner_seller_id: str | None = None
    next_follow_up_at: datetime | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    category: str | None = None
    notes: str | None = None
    status_crm: CRMStatus | None = None
    owner_seller_id: str | None = None
    next_follow_up_at: datetime | None = None
    # Fakturační údaje
    ico: str | None = None
    dic: str | None = None
    billing_address: str | None = None
    bank_account: str | None = None
    contact_person: str | None = None
    # Logo firmy
    logo_url: str | None = None


class BusinessResponse(BaseModel):
    id: str
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    category: str | None = None
    notes: str | None = None
    status_crm: str
    owner_seller_id: str | None = None
    owner_seller_name: str | None = None
    next_follow_up_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Fakturační údaje
    ico: str | None = None
    dic: str | None = None
    billing_address: str | None = None
    bank_account: str | None = None
    contact_person: str | None = None
    # Logo firmy
    logo_url: str | None = None


class BusinessListResponse(BaseModel):
    items: list[BusinessResponse]
    total: int
    page: int
    limit: int


# Activity schemas
class ActivityCreate(BaseModel):
    activity_type: ActivityType
    description: str
    outcome: str | None = None
    new_status: CRMStatus | None = None
    next_follow_up_at: datetime | None = None


class ActivityResponse(BaseModel):
    id: str
    business_id: str
    seller_id: str
    seller_name: str | None = None
    activity_type: str
    description: str
    outcome: str | None = None
    duration_minutes: int | None = None
    created_at: datetime | None = None


# Dashboard schemas
class TodayTask(BaseModel):
    id: str
    business_id: str
    business_name: str
    phone: str | None = None
    status_crm: str
    next_follow_up_at: datetime | None = None
    last_activity: str | None = None


class TodayTasksResponse(BaseModel):
    tasks: list[TodayTask]
    total: int


class CRMStats(BaseModel):
    total_leads: int
    new_leads: int
    calling: int
    interested: int
    offer_sent: int
    won: int
    lost: int
    dnc: int
    follow_ups_today: int


class PendingProjectInfo(BaseModel):
    """Rozpracovaný projekt pro dashboard."""
    id: str
    business_id: str
    business_name: str
    status: str
    package: str
    latest_version_number: int | None = None
    latest_version_date: datetime | None = None


class UnpaidClientInvoice(BaseModel):
    """Nezaplacená faktura od klienta."""
    id: str
    business_id: str
    business_name: str
    invoice_number: str
    amount_total: float
    due_date: datetime
    days_overdue: int  # záporné = dní do splatnosti, kladné = dní po splatnosti


class SellerDashboard(BaseModel):
    available_balance: float
    pending_projects_amount: float
    recent_invoices: list[dict]
    weekly_rewards: list[dict]
    # Nová pole pro redesign
    pending_projects: list[PendingProjectInfo] = []
    unpaid_client_invoices: list[UnpaidClientInvoice] = []
    total_leads: int = 0
    follow_ups_today: int = 0


# Project schemas
class ProjectStatus(str, Enum):
    offer = "offer"
    won = "won"
    in_production = "in_production"
    delivered = "delivered"
    live = "live"
    cancelled = "cancelled"


class PackageType(str, Enum):
    start = "start"
    profi = "profi"
    premium = "premium"
    custom = "custom"


class ProjectCreate(BaseModel):
    package: PackageType = PackageType.start
    status: ProjectStatus = ProjectStatus.offer
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None


class ProjectUpdate(BaseModel):
    package: PackageType | None = None
    status: ProjectStatus | None = None
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None


class ProjectResponse(BaseModel):
    id: str
    business_id: str
    package: str
    status: str
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Website Version schemas
class WebsiteVersionStatus(str, Enum):
    created = "created"
    generating = "generating"
    ready = "ready"
    failed = "failed"
    archived = "archived"


class WebsiteVersionCreate(BaseModel):
    project_id: str
    source_bundle_path: str | None = None
    preview_image_path: str | None = None
    notes: str | None = None


class WebsiteVersionResponse(BaseModel):
    id: str
    project_id: str
    version_number: int
    status: str
    source_bundle_path: str | None = None
    preview_image_path: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None


class WebsiteVersionListResponse(BaseModel):
    items: list[WebsiteVersionResponse]
    total: int


# Asset schemas
class ProjectAssetCreate(BaseModel):
    project_id: str
    type: str  # logo, photos, contract, etc.
    file_path: str
    filename: str
    mime_type: str
    size_bytes: int


class ProjectAssetResponse(BaseModel):
    id: str
    project_id: str
    type: str
    file_path: str
    filename: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime | None = None
    uploaded_by: str | None = None


# Ledger entries for account movements
class LedgerEntryResponse(BaseModel):
    id: str
    entry_type: str
    amount: float
    description: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    related_project_id: str | None = None
    related_business_id: str | None = None


class WeeklyRewardSummary(BaseModel):
    week: str
    amount: float
    count: int


class BalancePageResponse(BaseModel):
    available_balance: float
    ledger_entries: list[LedgerEntryResponse]
    weekly_rewards: list[WeeklyRewardSummary]


# ARES API schemas
class ARESAddress(BaseModel):
    nazevStatu: str | None = None
    nazevKraje: str | None = None
    nazevOkresu: str | None = None
    nazevObce: str | None = None
    nazevUlice: str | None = None
    cisloDomovni: int | None = None
    cisloOrientacni: int | None = None
    cisloOrientacniPismeno: str | None = None
    psc: int | None = None
    textovaAdresa: str | None = None


class ARESCompany(BaseModel):
    ico: str
    obchodniJmeno: str
    sidlo: ARESAddress | None = None
    pravniForma: str | None = None
    dic: str | None = None
