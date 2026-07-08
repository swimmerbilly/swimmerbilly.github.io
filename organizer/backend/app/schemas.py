from datetime import datetime

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
    created_at: datetime
    updated_at: datetime


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
