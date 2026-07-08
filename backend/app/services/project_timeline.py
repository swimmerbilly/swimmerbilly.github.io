from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Call, Email, Project, TextMessage, Voicemail


def build_project_timeline(db: Session, project_id: int, limit: int = 50) -> list[dict]:
    project = db.get(Project, project_id)
    if not project:
        return []

    entries: list[dict] = []

    for email in db.query(Email).filter(Email.project_id == project_id).all():
        entries.append(
            {
                "type": "email",
                "id": email.id,
                "occurred_at": email.received_at,
                "title": email.subject or "(no subject)",
                "summary": f"{'From' if email.direction.value == 'inbound' else 'To'} {email.from_address if email.direction.value == 'inbound' else email.to_address}",
                "body_preview": email.body[:200] if email.body else None,
                "meta": {
                    "direction": email.direction.value,
                    "is_read": email.is_read,
                    "account_label": email.account_label,
                },
            }
        )

    for text in db.query(TextMessage).filter(TextMessage.project_id == project_id).all():
        entries.append(
            {
                "type": "text",
                "id": text.id,
                "occurred_at": text.sent_at,
                "title": f"Text — {text.contact_name or text.phone_number}",
                "summary": text.body[:200],
                "body_preview": None,
                "meta": {"direction": text.direction.value, "is_read": text.is_read},
            }
        )

    for call in db.query(Call).filter(Call.project_id == project_id).all():
        role = f" ({call.caller_role})" if call.caller_role else ""
        entries.append(
            {
                "type": "call",
                "id": call.id,
                "occurred_at": call.called_at,
                "title": f"Call — {call.contact_name or call.phone_number}{role}",
                "summary": call.notes[:200] if call.notes else "No notes recorded",
                "body_preview": call.notes,
                "meta": {
                    "caller_role": call.caller_role,
                    "follow_up_at": call.follow_up_at.isoformat() if call.follow_up_at else None,
                    "follow_up_completed": call.follow_up_completed,
                },
            }
        )

    for vm in db.query(Voicemail).filter(Voicemail.project_id == project_id).all():
        entries.append(
            {
                "type": "voicemail",
                "id": vm.id,
                "occurred_at": vm.received_at,
                "title": f"Voicemail — {vm.contact_name or vm.phone_number}",
                "summary": (vm.transcript or "No transcript")[:200],
                "body_preview": vm.transcript,
                "meta": {"is_listened": vm.is_listened},
            }
        )

    entries.sort(key=lambda e: e["occurred_at"], reverse=True)

    result = []
    for entry in entries[:limit]:
        occurred = entry["occurred_at"]
        result.append(
            {
                **entry,
                "occurred_at": occurred.isoformat() if isinstance(occurred, datetime) else occurred,
            }
        )
    return result
