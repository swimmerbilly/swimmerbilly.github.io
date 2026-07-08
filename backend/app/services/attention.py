from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Call, Email, Project, ProjectStatus, TextMessage, Voicemail


def build_attention_queue(db: Session, limit: int = 15) -> list[dict]:
    """Prioritized items that need the user's attention."""
    items: list[dict] = []
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    for vm in (
        db.query(Voicemail)
        .filter(Voicemail.is_listened.is_(False))
        .order_by(Voicemail.received_at.desc())
        .limit(5)
        .all()
    ):
        items.append(
            {
                "priority": 1,
                "type": "voicemail",
                "id": vm.id,
                "title": f"Voicemail from {vm.contact_name or vm.phone_number}",
                "detail": (vm.transcript or "No transcript")[:120],
                "href": "/voicemails",
                "occurred_at": vm.received_at.isoformat(),
            }
        )

    for email in (
        db.query(Email)
        .filter(Email.is_read.is_(False))
        .order_by(Email.received_at.desc())
        .limit(5)
        .all()
    ):
        items.append(
            {
                "priority": 2,
                "type": "email",
                "id": email.id,
                "title": email.subject or "(no subject)",
                "detail": f"From {email.from_address}",
                "href": "/emails",
                "occurred_at": email.received_at.isoformat(),
            }
        )

    for text in (
        db.query(TextMessage)
        .filter(TextMessage.is_read.is_(False))
        .order_by(TextMessage.sent_at.desc())
        .limit(3)
        .all()
    ):
        items.append(
            {
                "priority": 3,
                "type": "text",
                "id": text.id,
                "title": f"Text from {text.contact_name or text.phone_number}",
                "detail": text.body[:120],
                "href": "/texts",
                "occurred_at": text.sent_at.isoformat(),
            }
        )

    for call in (
        db.query(Call)
        .filter(
            Call.follow_up_at.isnot(None),
            Call.follow_up_completed.is_(False),
            Call.follow_up_at <= now + timedelta(days=1),
        )
        .order_by(Call.follow_up_at.asc())
        .limit(5)
        .all()
    ):
        items.append(
            {
                "priority": 1,
                "type": "follow_up",
                "id": call.id,
                "title": f"Follow up with {call.contact_name or 'contact'}",
                "detail": (call.notes or "Call follow-up due")[:120],
                "href": f"/projects/{call.project_id}" if call.project_id else "/calls",
                "occurred_at": call.follow_up_at.isoformat() if call.follow_up_at else now.isoformat(),
            }
        )

    for call in (
        db.query(Call)
        .filter(
            (Call.notes.is_(None)) | (Call.notes == ""),
            Call.called_at >= week_ago,
        )
        .order_by(Call.called_at.desc())
        .limit(3)
        .all()
    ):
        items.append(
            {
                "priority": 4,
                "type": "call_no_notes",
                "id": call.id,
                "title": f"Call missing notes — {call.contact_name or call.phone_number}",
                "detail": "Add notes so you remember what was discussed.",
                "href": "/calls",
                "occurred_at": call.called_at.isoformat(),
            }
        )

    active_projects = (
        db.query(Project)
        .filter(Project.status == ProjectStatus.ACTIVE)
        .all()
    )
    for project in active_projects:
        activity_dates: list[datetime] = []
        for model, col, fk in [
            (Email, Email.received_at, Email.project_id),
            (Call, Call.called_at, Call.project_id),
            (TextMessage, TextMessage.sent_at, TextMessage.project_id),
            (Voicemail, Voicemail.received_at, Voicemail.project_id),
        ]:
            row = (
                db.query(col)
                .filter(fk == project.id)
                .order_by(col.desc())
                .first()
            )
            if row and row[0]:
                activity_dates.append(row[0])

        last_activity = max(activity_dates) if activity_dates else None
        if last_activity is None or last_activity < month_ago:
            items.append(
                {
                    "priority": 5,
                    "type": "stale_project",
                    "id": project.id,
                    "title": f"No recent activity — {project.name}",
                    "detail": "Check in or update status in Harvest.",
                    "href": f"/projects/{project.id}",
                    "occurred_at": (last_activity or project.updated_at).isoformat(),
                }
            )

    unlinked_count = (
        db.query(Email).filter(Email.project_id.is_(None)).count()
        + db.query(TextMessage).filter(TextMessage.project_id.is_(None)).count()
        + db.query(Voicemail).filter(Voicemail.project_id.is_(None)).count()
    )
    if unlinked_count >= 3:
        items.append(
            {
                "priority": 4,
                "type": "unlinked_comms",
                "id": 0,
                "title": f"{unlinked_count} communications not linked to a project",
                "detail": "Link them so your briefs and timelines stay accurate.",
                "href": "/emails",
                "occurred_at": now.isoformat(),
            }
        )

    items.sort(key=lambda item: (item["priority"], item["occurred_at"]))
    return items[:limit]
