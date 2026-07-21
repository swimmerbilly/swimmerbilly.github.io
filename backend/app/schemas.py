from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import CommunicationDirection, ProjectStatus, CallerRole


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: str = "#3b82f6"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None
    color: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    harvest_id: int | None = None
    harvest_client_name: str | None = None
    harvest_code: str | None = None
    harvest_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class HarvestStatus(BaseModel):
    configured: bool
    account_id: str | None = None
    user_name: str | None = None


class HarvestSyncResult(BaseModel):
    synced: int
    created: int
    updated: int
    archived: int


class GrasshopperStatus(BaseModel):
    configured: bool
    imap_configured: bool
    webhook_configured: bool
    imap_host: str | None = None
    imap_user: str | None = None
    imap_folder: str | None = None
    webhook_url_hint: str | None = None
    uses_work_outlook: bool = False


class GrasshopperSyncResult(BaseModel):
    emails_scanned: int
    events_found: int
    voicemails_created: int
    calls_created: int
    texts_created: int
    skipped: int


class GrasshopperWebhookEvent(BaseModel):
    type: Literal["voicemail", "call", "text"]
    phone_number: str
    contact_name: str | None = None
    body: str | None = None
    transcript: str | None = None
    duration_seconds: int | None = None
    received_at: datetime | None = None
    message_id: str | None = None


class MailboxStatus(BaseModel):
    label: str
    provider: str
    configured: bool
    host: str | None = None
    user: str | None = None
    folder: str | None = None


class MailboxAccountSyncResult(BaseModel):
    account: str
    messages_scanned: int
    created: int
    skipped: int


class MailboxSyncResult(BaseModel):
    accounts_synced: int
    results: list[MailboxAccountSyncResult]
    created: int
    skipped: int


class EmailBase(BaseModel):
    project_id: int | None = None
    direction: CommunicationDirection = CommunicationDirection.INBOUND
    from_address: str
    to_address: str
    subject: str = ""
    body: str = ""
    is_read: bool = False
    is_starred: bool = False
    received_at: datetime | None = None


class EmailCreate(EmailBase):
    pass


class EmailUpdate(BaseModel):
    project_id: int | None = None
    is_read: bool | None = None
    is_starred: bool | None = None


class EmailRead(EmailBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_label: str | None = None
    external_message_id: str | None = None
    project_name: str | None = None
    project_color: str | None = None
    received_at: datetime
    created_at: datetime


class TextBase(BaseModel):
    project_id: int | None = None
    direction: CommunicationDirection = CommunicationDirection.INBOUND
    contact_name: str | None = None
    phone_number: str
    body: str
    is_read: bool = False
    sent_at: datetime | None = None


class TextCreate(TextBase):
    pass


class TextUpdate(BaseModel):
    project_id: int | None = None
    is_read: bool | None = None


class TextRead(TextBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grasshopper_message_id: str | None = None
    project_name: str | None = None
    project_color: str | None = None
    sent_at: datetime
    created_at: datetime


class CallBase(BaseModel):
    project_id: int | None = None
    direction: CommunicationDirection = CommunicationDirection.INBOUND
    contact_name: str | None = None
    caller_role: CallerRole | None = None
    phone_number: str
    duration_seconds: int | None = None
    notes: str | None = None
    called_at: datetime | None = None


class CallCreate(CallBase):
    pass


class QuickCallNoteCreate(BaseModel):
    project_id: int
    contact_name: str = Field(min_length=1, max_length=200)
    caller_role: CallerRole | None = None
    notes: str = Field(min_length=1)
    phone_number: str | None = Field(default=None, max_length=30)
    follow_up_days: int | None = Field(default=None, ge=1, le=90)


class CallUpdate(BaseModel):
    project_id: int | None = None
    caller_role: CallerRole | None = None
    notes: str | None = None
    follow_up_completed: bool | None = None


class CallRead(CallBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grasshopper_message_id: str | None = None
    project_name: str | None = None
    project_color: str | None = None
    follow_up_at: datetime | None = None
    follow_up_completed: bool = False
    called_at: datetime
    created_at: datetime


class VoicemailBase(BaseModel):
    project_id: int | None = None
    contact_name: str | None = None
    phone_number: str
    transcript: str | None = None
    audio_path: str | None = None
    duration_seconds: int | None = None
    is_listened: bool = False
    received_at: datetime | None = None


class VoicemailCreate(VoicemailBase):
    pass


class VoicemailUpdate(BaseModel):
    project_id: int | None = None
    is_listened: bool | None = None
    transcript: str | None = None


class VoicemailRead(VoicemailBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grasshopper_message_id: str | None = None
    project_name: str | None = None
    project_color: str | None = None
    received_at: datetime
    created_at: datetime


class DashboardStats(BaseModel):
    project_count: int
    active_projects: int
    unread_emails: int
    unread_texts: int
    unlistened_voicemails: int
    recent_calls: int
    total_communications: int


class AssistantStatus(BaseModel):
    configured: bool
    model: str
    name: str


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    priority: str
    is_completed: bool
    is_user_added: bool
    sort_order: int
    created_at: datetime


class ChecklistItemCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ChecklistItemUpdate(BaseModel):
    is_completed: bool | None = None


class DayPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_date: str
    greeting: str
    today_focus: list[str]
    week_focus: list[str]
    month_focus: list[str]
    generated_at: datetime
    checklist_items: list[ChecklistItemRead]
    wrap_up_summary: str | None = None
    wrap_up_tomorrow: list[str] = []
    wrap_up_completed: list[str] = []
    wrap_up_slipped: list[str] = []
    wrap_up_generated_at: datetime | None = None
    weekly_review_stalled: list[str] = []
    weekly_review_gaps: list[str] = []
    weekly_review_priorities: list[str] = []
    weekly_review_generated_at: datetime | None = None

    @classmethod
    def from_model(cls, plan: "DayPlan") -> "DayPlanRead":
        import json

        from app.models import DayPlan as DayPlanModel

        assert isinstance(plan, DayPlanModel)

        wrap_data: dict = {}
        try:
            parsed = json.loads(plan.wrap_up_tomorrow or "{}")
            if isinstance(parsed, list):
                wrap_data = {"tomorrow": parsed}
            elif isinstance(parsed, dict):
                wrap_data = parsed
        except json.JSONDecodeError:
            wrap_data = {}

        return cls(
            id=plan.id,
            plan_date=plan.plan_date,
            greeting=plan.greeting,
            today_focus=json.loads(plan.today_focus or "[]"),
            week_focus=json.loads(plan.week_focus or "[]"),
            month_focus=json.loads(plan.month_focus or "[]"),
            generated_at=plan.generated_at,
            checklist_items=sorted(
                [ChecklistItemRead.model_validate(i) for i in plan.checklist_items],
                key=lambda item: item.sort_order,
            ),
            wrap_up_summary=plan.wrap_up_summary,
            wrap_up_tomorrow=wrap_data.get("tomorrow", []),
            wrap_up_completed=wrap_data.get("completed", []),
            wrap_up_slipped=wrap_data.get("slipped", []),
            wrap_up_generated_at=plan.wrap_up_generated_at,
            weekly_review_stalled=json.loads(plan.weekly_review_stalled or "[]"),
            weekly_review_gaps=json.loads(plan.weekly_review_gaps or "[]"),
            weekly_review_priorities=json.loads(plan.weekly_review_priorities or "[]"),
            weekly_review_generated_at=plan.weekly_review_generated_at,
        )


class AssistantMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class AssistantConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: int | None = None
    context: dict | None = None


class AssistantAction(BaseModel):
    type: str
    label: str
    params: dict = {}


class AssistantActionResult(BaseModel):
    success: bool
    message: str


class AssistantChatResponse(BaseModel):
    conversation: AssistantConversationRead
    user_message: AssistantMessageRead
    assistant_message: AssistantMessageRead
    actions: list[AssistantAction] = []


class SetupField(BaseModel):
    key: str
    label: str
    value: str | None = None
    masked: str | None = None
    has_value: bool = False
    placeholder: str = ""
    secret: bool = False


class SetupStep(BaseModel):
    id: str
    title: str
    description: str
    configured: bool
    fields: list[SetupField]
    help_url: str | None = None
    help_text: str | None = None
    optional: bool = False


class SetupStatus(BaseModel):
    steps: list[SetupStep]
    required_configured: bool
    any_email_configured: bool


class SetupStepSave(BaseModel):
    values: dict[str, str] = {}


class AttentionItem(BaseModel):
    priority: int
    type: str
    id: int
    title: str
    detail: str
    href: str
    occurred_at: str


class TimelineEntry(BaseModel):
    type: str
    id: int
    occurred_at: str
    title: str
    summary: str
    body_preview: str | None = None
    meta: dict = {}


class ProjectContact(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    roles: list[str] = []
    sources: list[str] = []
    touch_count: int = 0


class ProjectSuggestion(BaseModel):
    project_id: int
    project_name: str
    confidence: float


class LinkSuggestion(BaseModel):
    comm_type: str
    comm_id: int
    title: str
    suggestion: ProjectSuggestion


class LinkCommRequest(BaseModel):
    comm_type: str = Field(pattern=r"^(email|text|voicemail|call)$")
    comm_id: int
    project_id: int


class JurisdictionRead(BaseModel):
    id: str
    name: str
    kind: str
    system: str
    portal_url: str
    search_url: str | None = None
    notes: str = ""
    crawlable: bool = False


class BuildingPermitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jurisdiction_id: str
    external_id: str
    permit_number: str
    permit_type: str | None = None
    status: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    parcel_number: str | None = None
    applied_at: datetime | None = None
    issued_at: datetime | None = None
    estimated_value: str | None = None
    has_structural_plans: bool = False
    structural_signals: list[str] = []
    structural_engineer_name: str | None = None
    structural_engineer_license: str | None = None
    structural_engineer_firm: str | None = None
    source_url: str | None = None
    source_system: str
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, permit: "BuildingPermit") -> "BuildingPermitRead":
        import json

        from app.models import BuildingPermit as BuildingPermitModel

        assert isinstance(permit, BuildingPermitModel)
        signals: list[str] = []
        if permit.structural_signals:
            try:
                parsed = json.loads(permit.structural_signals)
                if isinstance(parsed, list):
                    signals = [str(s) for s in parsed]
            except json.JSONDecodeError:
                signals = []
        return cls(
            id=permit.id,
            jurisdiction_id=permit.jurisdiction_id,
            external_id=permit.external_id,
            permit_number=permit.permit_number,
            permit_type=permit.permit_type,
            status=permit.status,
            description=permit.description,
            address=permit.address,
            city=permit.city,
            parcel_number=permit.parcel_number,
            applied_at=permit.applied_at,
            issued_at=permit.issued_at,
            estimated_value=permit.estimated_value,
            has_structural_plans=permit.has_structural_plans,
            structural_signals=signals,
            structural_engineer_name=permit.structural_engineer_name,
            structural_engineer_license=permit.structural_engineer_license,
            structural_engineer_firm=permit.structural_engineer_firm,
            source_url=permit.source_url,
            source_system=permit.source_system,
            last_seen_at=permit.last_seen_at,
            created_at=permit.created_at,
            updated_at=permit.updated_at,
        )


class PermitSyncRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jurisdiction_id: str
    status: str
    records_found: int
    records_upserted: int
    structural_found: int
    message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


class PermitImportRequest(BaseModel):
    permits: list[dict] = Field(default_factory=list)


class PermitImportResult(BaseModel):
    created: int
    updated: int
    structural_found: int


class PermitStats(BaseModel):
    total: int
    with_structural_plans: int
    with_engineer_named: int
    by_jurisdiction: dict[str, int]

