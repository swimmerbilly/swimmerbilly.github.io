import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models import Call, Email, Project, ProjectStatus, TextMessage, Voicemail


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _score_project(project: Project, haystack: str) -> float:
    score = 0.0
    name = _normalize(project.name)
    client = _normalize(project.harvest_client_name or "")
    code = _normalize(project.harvest_code or "")

    if name and name in haystack:
        score += 0.6
    if client and client in haystack:
        score += 0.4
    if code and code in haystack:
        score += 0.3

    for token in name.split():
        if len(token) > 3 and token in haystack:
            score += 0.15

    ratio = SequenceMatcher(None, name, haystack).ratio()
    score += ratio * 0.2
    return min(score, 1.0)


def _haystack_for_email(email: Email) -> str:
    return _normalize(f"{email.subject} {email.body} {email.from_address}")


def _haystack_for_text(text: TextMessage) -> str:
    return _normalize(f"{text.body} {text.contact_name or ''} {text.phone_number}")


def _haystack_for_voicemail(vm: Voicemail) -> str:
    return _normalize(f"{vm.transcript or ''} {vm.contact_name or ''} {vm.phone_number}")


def _haystack_for_call(call: Call) -> str:
    return _normalize(f"{call.notes or ''} {call.contact_name or ''} {call.phone_number}")


def suggest_project_for_comm(
    db: Session,
    comm_type: str,
    comm_id: int,
    limit: int = 3,
) -> list[dict]:
    entity = None
    haystack = ""

    if comm_type == "email":
        entity = db.get(Email, comm_id)
        if entity:
            haystack = _haystack_for_email(entity)
    elif comm_type == "text":
        entity = db.get(TextMessage, comm_id)
        if entity:
            haystack = _haystack_for_text(entity)
    elif comm_type == "voicemail":
        entity = db.get(Voicemail, comm_id)
        if entity:
            haystack = _haystack_for_voicemail(entity)
    elif comm_type == "call":
        entity = db.get(Call, comm_id)
        if entity:
            haystack = _haystack_for_call(entity)
    else:
        return []

    if not entity or not haystack:
        return []

    if getattr(entity, "project_id", None):
        return []

    projects = (
        db.query(Project)
        .filter(Project.status == ProjectStatus.ACTIVE)
        .order_by(Project.updated_at.desc())
        .all()
    )

    scored = []
    for project in projects:
        score = _score_project(project, haystack)
        if score >= 0.25:
            scored.append(
                {
                    "project_id": project.id,
                    "project_name": project.name,
                    "confidence": round(score, 2),
                }
            )

    scored.sort(key=lambda s: s["confidence"], reverse=True)
    return scored[:limit]


def suggest_unlinked_comms(db: Session, limit: int = 20) -> list[dict]:
    suggestions = []

    for email in (
        db.query(Email)
        .filter(Email.project_id.is_(None))
        .order_by(Email.received_at.desc())
        .limit(limit)
        .all()
    ):
        top = suggest_project_for_comm(db, "email", email.id, limit=1)
        if top:
            suggestions.append(
                {
                    "comm_type": "email",
                    "comm_id": email.id,
                    "title": email.subject or "(no subject)",
                    "suggestion": top[0],
                }
            )

    for text in (
        db.query(TextMessage)
        .filter(TextMessage.project_id.is_(None))
        .order_by(TextMessage.sent_at.desc())
        .limit(limit)
        .all()
    ):
        top = suggest_project_for_comm(db, "text", text.id, limit=1)
        if top:
            suggestions.append(
                {
                    "comm_type": "text",
                    "comm_id": text.id,
                    "title": f"Text from {text.contact_name or text.phone_number}",
                    "suggestion": top[0],
                }
            )

    for vm in (
        db.query(Voicemail)
        .filter(Voicemail.project_id.is_(None))
        .order_by(Voicemail.received_at.desc())
        .limit(limit)
        .all()
    ):
        top = suggest_project_for_comm(db, "voicemail", vm.id, limit=1)
        if top:
            suggestions.append(
                {
                    "comm_type": "voicemail",
                    "comm_id": vm.id,
                    "title": f"Voicemail from {vm.contact_name or vm.phone_number}",
                    "suggestion": top[0],
                }
            )

    return suggestions[:limit]


def link_comm_to_project(db: Session, comm_type: str, comm_id: int, project_id: int) -> bool:
    project = db.get(Project, project_id)
    if not project:
        return False

    entity = None
    if comm_type == "email":
        entity = db.get(Email, comm_id)
    elif comm_type == "text":
        entity = db.get(TextMessage, comm_id)
    elif comm_type == "voicemail":
        entity = db.get(Voicemail, comm_id)
    elif comm_type == "call":
        entity = db.get(Call, comm_id)

    if not entity:
        return False

    entity.project_id = project_id
    db.commit()
    return True
