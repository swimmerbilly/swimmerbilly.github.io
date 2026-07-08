from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Call, Email, Project, ProjectStatus, TextMessage, Voicemail
from app.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    week_ago = datetime.utcnow() - timedelta(days=7)

    project_count = db.query(func.count(Project.id)).scalar() or 0
    active_projects = (
        db.query(func.count(Project.id))
        .filter(Project.status == ProjectStatus.ACTIVE)
        .scalar()
        or 0
    )
    unread_emails = (
        db.query(func.count(Email.id)).filter(Email.is_read.is_(False)).scalar() or 0
    )
    unread_texts = (
        db.query(func.count(TextMessage.id))
        .filter(TextMessage.is_read.is_(False))
        .scalar()
        or 0
    )
    unlistened_voicemails = (
        db.query(func.count(Voicemail.id))
        .filter(Voicemail.is_listened.is_(False))
        .scalar()
        or 0
    )
    recent_calls = (
        db.query(func.count(Call.id)).filter(Call.called_at >= week_ago).scalar() or 0
    )

    total_communications = (
        (db.query(func.count(Email.id)).scalar() or 0)
        + (db.query(func.count(TextMessage.id)).scalar() or 0)
        + (db.query(func.count(Call.id)).scalar() or 0)
        + (db.query(func.count(Voicemail.id)).scalar() or 0)
    )

    return DashboardStats(
        project_count=project_count,
        active_projects=active_projects,
        unread_emails=unread_emails,
        unread_texts=unread_texts,
        unlistened_voicemails=unlistened_voicemails,
        recent_calls=recent_calls,
        total_communications=total_communications,
    )
