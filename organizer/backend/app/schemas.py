from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import CommunicationDirection, ProjectStatus


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
    sent_at: datetime
    created_at: datetime


class CallBase(BaseModel):
    project_id: int | None = None
    direction: CommunicationDirection = CommunicationDirection.INBOUND
    contact_name: str | None = None
    phone_number: str
    duration_seconds: int | None = None
    notes: str | None = None
    called_at: datetime | None = None


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    project_id: int | None = None
    notes: str | None = None


class CallRead(CallBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grasshopper_message_id: str | None = None
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


class AssistantChatResponse(BaseModel):
    conversation: AssistantConversationRead
    user_message: AssistantMessageRead
    assistant_message: AssistantMessageRead

