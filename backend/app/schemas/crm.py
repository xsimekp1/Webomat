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


class DomainStatus(str, Enum):
    planned = "planned"
    purchased = "purchased"
    deployed = "deployed"
    not_needed = "not_needed"
    other = "other"


class ProjectCreate(BaseModel):
    package: PackageType = PackageType.start
    status: ProjectStatus = ProjectStatus.offer
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None
    # New fields
    required_deadline: datetime | None = None
    budget: float | None = None
    domain_status: DomainStatus = DomainStatus.planned
    internal_notes: str | None = None
    client_notes: str | None = None


class ProjectUpdate(BaseModel):
    package: PackageType | None = None
    status: ProjectStatus | None = None
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None
    # New fields
    required_deadline: datetime | None = None
    budget: float | None = None
    domain_status: DomainStatus | None = None
    internal_notes: str | None = None
    client_notes: str | None = None


class ProjectResponse(BaseModel):
    id: str
    business_id: str
    package: str
    status: str
    price_setup: float | None = None
    price_monthly: float | None = None
    domain: str | None = None
    notes: str | None = None
    # New fields
    required_deadline: datetime | None = None
    budget: float | None = None
    domain_status: str | None = None
    internal_notes: str | None = None
    client_notes: str | None = None
    # Version info
    versions_count: int | None = None
    latest_version_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Website Version schemas
class WebsiteVersionStatus(str, Enum):
    created = "created"
    generating = "generating"
    ready = "ready"
    failed = "failed"
    archived = "archived"


class DeploymentStatus(str, Enum):
    none = "none"
    deploying = "deploying"
    deployed = "deployed"
    failed = "failed"
    unpublished = "unpublished"


class WebsiteVersionCreate(BaseModel):
    # Note: project_id comes from URL path parameter, not request body
    source_bundle_path: str | None = None
    preview_image_path: str | None = None
    notes: str | None = None
    html_content: str | None = None
    html_content_en: str | None = None
    thumbnail_url: str | None = None
    parent_version_id: str | None = None
    generation_instructions: str | None = None


class WebsiteVersionUpdate(BaseModel):
    status: WebsiteVersionStatus | None = None
    notes: str | None = None
    html_content: str | None = None
    html_content_en: str | None = None
    is_current: bool | None = None
    generation_instructions: str | None = None


class WebsiteVersionResponse(BaseModel):
    id: str
    project_id: str
    version_number: int
    status: str
    source_bundle_path: str | None = None
    preview_image_path: str | None = None
    notes: str | None = None
    # New fields
    html_content: str | None = None
    html_content_en: str | None = None
    thumbnail_url: str | None = None
    screenshot_desktop_url: str | None = None
    screenshot_mobile_url: str | None = None
    public_url: str | None = None
    deployment_status: str | None = None
    deployment_platform: str | None = None
    deployment_id: str | None = None
    is_current: bool | None = None
    published_at: datetime | None = None
    parent_version_id: str | None = None
    generation_instructions: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None


class WebsiteVersionListResponse(BaseModel):
    items: list[WebsiteVersionResponse]
    total: int


# Version Comments schemas
class CommentAuthorType(str, Enum):
    client = "client"
    internal = "internal"


class CommentStatus(str, Enum):
    new = "new"
    acknowledged = "acknowledged"
    resolved = "resolved"
    rejected = "rejected"


class CommentAnchorType(str, Enum):
    element = "element"
    coordinates = "coordinates"
    general = "general"


class VersionCommentCreate(BaseModel):
    content: str
    author_type: CommentAuthorType = CommentAuthorType.client
    author_name: str | None = None
    author_email: str | None = None
    anchor_type: CommentAnchorType | None = None
    anchor_selector: str | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None


class VersionCommentUpdate(BaseModel):
    status: CommentStatus | None = None
    resolution_note: str | None = None


class VersionCommentResponse(BaseModel):
    id: str
    version_id: str
    author_type: str
    author_name: str | None = None
    author_email: str | None = None
    content: str
    anchor_type: str | None = None
    anchor_selector: str | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_note: str | None = None
    created_at: datetime | None = None


# Preview Share Link schemas
class ShareLinkCreate(BaseModel):
    expires_in_days: int | None = 7
    max_views: int | None = None


class ShareLinkResponse(BaseModel):
    id: str
    version_id: str
    token: str
    expires_at: datetime | None = None
    view_count: int
    max_views: int | None = None
    is_active: bool
    created_at: datetime | None = None
    # Computed URL
    preview_url: str | None = None


# Platform Feedback schemas
class FeedbackCategory(str, Enum):
    bug = "bug"
    idea = "idea"
    ux = "ux"
    other = "other"


class FeedbackPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class FeedbackStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    rejected = "rejected"


class PlatformFeedbackCreate(BaseModel):
    content: str
    category: FeedbackCategory = FeedbackCategory.idea
    priority: FeedbackPriority = FeedbackPriority.medium
    page_url: str | None = None


class PlatformFeedbackUpdate(BaseModel):
    status: FeedbackStatus | None = None
    admin_note: str | None = None


class PlatformFeedbackResponse(BaseModel):
    id: str
    submitted_by: str
    submitter_name: str | None = None
    content: str
    category: str
    priority: str
    status: str
    admin_note: str | None = None
    handled_by: str | None = None
    handler_name: str | None = None
    handled_at: datetime | None = None
    page_url: str | None = None
    created_at: datetime | None = None


# Background Jobs schemas
class JobType(str, Enum):
    screenshot_capture = "screenshot_capture"
    deploy_version = "deploy_version"
    undeploy_version = "undeploy_version"
    generate_thumbnail = "generate_thumbnail"
    send_notification = "send_notification"
    cleanup_expired_links = "cleanup_expired_links"


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class BackgroundJobResponse(BaseModel):
    id: str
    job_type: str
    payload: dict | None = None
    status: str
    priority: int
    attempts: int
    max_attempts: int
    result: dict | None = None
    error_message: str | None = None
    scheduled_for: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None


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
