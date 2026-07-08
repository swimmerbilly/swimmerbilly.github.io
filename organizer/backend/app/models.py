import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CommunicationDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    harvest_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False
    )
    color: Mapped[str] = mapped_column(String(7), default="#3b82f6")
    harvest_client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    harvest_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    harvest_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    emails: Mapped[list["Email"]] = relationship(back_populates="project")
    texts: Mapped[list["TextMessage"]] = relationship(back_populates="project")
    calls: Mapped[list["Call"]] = relationship(back_populates="project")
    voicemails: Mapped[list["Voicemail"]] = relationship(back_populates="project")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    direction: Mapped[CommunicationDirection] = mapped_column(
        Enum(CommunicationDirection), default=CommunicationDirection.INBOUND
    )
    from_address: Mapped[str] = mapped_column(String(320), nullable=False)
    to_address: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="emails")


class TextMessage(Base):
    __tablename__ = "text_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    direction: Mapped[CommunicationDirection] = mapped_column(
        Enum(CommunicationDirection), default=CommunicationDirection.INBOUND
    )
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="texts")


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    direction: Mapped[CommunicationDirection] = mapped_column(
        Enum(CommunicationDirection), default=CommunicationDirection.INBOUND
    )
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    called_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="calls")


class Voicemail(Base):
    __tablename__ = "voicemails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_listened: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="voicemails")
