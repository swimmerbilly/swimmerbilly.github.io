from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Call, Email, Project, ProjectStatus, TextMessage, Voicemail


def build_workspace_context(db: Session) -> str:
    week_ago = datetime.utcnow() - timedelta(days=7)
    lines: list[str] = ["# Workspace snapshot", ""]

    active_projects = (
        db.query(Project)
        .filter(Project.status == ProjectStatus.ACTIVE)
        .order_by(Project.updated_at.desc())
        .limit(25)
        .all()
    )
    lines.append(f"## Active projects ({len(active_projects)} shown)")
    if active_projects:
        for project in active_projects:
            client = f" · client: {project.harvest_client_name}" if project.harvest_client_name else ""
            source = "Harvest" if project.harvest_id else "local"
            lines.append(f"- [{project.id}] {project.name} ({source}{client})")
    else:
        lines.append("- No active projects")

    unread_emails = (
        db.query(Email)
        .filter(Email.is_read.is_(False))
        .order_by(Email.received_at.desc())
        .limit(10)
        .all()
    )
    lines.extend(["", f"## Unread emails ({len(unread_emails)} recent)"])
    for email in unread_emails:
        preview = email.body[:120].replace("\n", " ") if email.body else ""
        lines.append(
            f"- [{email.id}] From {email.from_address}: {email.subject or '(no subject)'} — {preview}"
        )
    if not unread_emails:
        lines.append("- None")

    unread_texts = (
        db.query(TextMessage)
        .filter(TextMessage.is_read.is_(False))
        .order_by(TextMessage.sent_at.desc())
        .limit(10)
        .all()
    )
    lines.extend(["", f"## Unread texts ({len(unread_texts)} recent)"])
    for text in unread_texts:
        who = text.contact_name or text.phone_number
        lines.append(f"- [{text.id}] {who}: {text.body[:120]}")
    if not unread_texts:
        lines.append("- None")

    unlistened = (
        db.query(Voicemail)
        .filter(Voicemail.is_listened.is_(False))
        .order_by(Voicemail.received_at.desc())
        .limit(10)
        .all()
    )
    lines.extend(["", f"## Unlistened voicemails ({len(unlistened)} recent)"])
    for vm in unlistened:
        who = vm.contact_name or vm.phone_number
        transcript = (vm.transcript or "")[:120]
        lines.append(f"- [{vm.id}] {who}: {transcript or '(no transcript)'}")
    if not unlistened:
        lines.append("- None")

    recent_calls = (
        db.query(Call).filter(Call.called_at >= week_ago).order_by(Call.called_at.desc()).limit(10).all()
    )
    lines.extend(["", f"## Calls this week ({len(recent_calls)} recent)"])
    for call in recent_calls:
        who = call.contact_name or call.phone_number
        notes = (call.notes or "")[:80]
        lines.append(f"- [{call.id}] {call.direction.value} call with {who}{': ' + notes if notes else ''}")
    if not recent_calls:
        lines.append("- None")

    return "\n".join(lines)
