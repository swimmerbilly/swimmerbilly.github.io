import hashlib
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Call, CommunicationDirection, TextMessage, Voicemail
from app.services.grasshopper_imap import GrasshopperError, fetch_grasshopper_emails, parse_grasshopper_messages
from app.services.grasshopper_parser import ParsedGrasshopperEvent

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / settings.grasshopper_upload_dir


def _save_audio(event: ParsedGrasshopperEvent) -> str | None:
    if not event.audio_bytes:
        return None

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(event.message_id.encode("utf-8")).hexdigest()[:12]
    filename = event.audio_filename or "voicemail.mp3"
    safe_name = re.sub(r"[^\w.\-]+", "_", filename)
    target = UPLOAD_ROOT / f"{digest}_{safe_name}"
    target.write_bytes(event.audio_bytes)
    return f"/uploads/grasshopper/{target.name}"


def _already_imported(db: Session, message_id: str) -> bool:
    return (
        db.query(Voicemail).filter(Voicemail.grasshopper_message_id == message_id).first() is not None
        or db.query(Call).filter(Call.grasshopper_message_id == message_id).first() is not None
        or db.query(TextMessage).filter(TextMessage.grasshopper_message_id == message_id).first() is not None
    )


def import_grasshopper_event(db: Session, event: ParsedGrasshopperEvent) -> str | None:
    if _already_imported(db, event.message_id):
        return None

    if event.event_type == "voicemail":
        voicemail = Voicemail(
            project_id=None,
            contact_name=event.contact_name,
            phone_number=event.phone_number,
            transcript=event.transcript,
            audio_path=_save_audio(event),
            duration_seconds=event.duration_seconds,
            is_listened=False,
            grasshopper_message_id=event.message_id,
            received_at=event.received_at,
        )
        db.add(voicemail)
        return "voicemail"

    if event.event_type == "call":
        call = Call(
            project_id=None,
            direction=CommunicationDirection.INBOUND,
            contact_name=event.contact_name,
            phone_number=event.phone_number,
            duration_seconds=event.duration_seconds,
            notes=event.body,
            grasshopper_message_id=event.message_id,
            called_at=event.received_at,
        )
        db.add(call)
        return "call"

    if event.event_type == "text":
        text = TextMessage(
            project_id=None,
            direction=CommunicationDirection.INBOUND,
            contact_name=event.contact_name,
            phone_number=event.phone_number,
            body=event.body or "",
            is_read=False,
            grasshopper_message_id=event.message_id,
            sent_at=event.received_at,
        )
        db.add(text)
        return "text"

    return None


def sync_grasshopper_from_imap(db: Session, since_days: int = 30) -> dict:
    messages = fetch_grasshopper_emails(since_days=since_days)
    events = parse_grasshopper_messages(messages)

    created = {"voicemail": 0, "call": 0, "text": 0}
    skipped = 0

    for event in events:
        imported_as = import_grasshopper_event(db, event)
        if imported_as:
            created[imported_as] += 1
        else:
            skipped += 1

    db.commit()

    return {
        "emails_scanned": len(messages),
        "events_found": len(events),
        "voicemails_created": created["voicemail"],
        "calls_created": created["call"],
        "texts_created": created["text"],
        "skipped": skipped,
    }


def import_grasshopper_webhook_event(db: Session, payload: dict) -> dict:
    event_type = payload.get("type")
    if event_type not in {"voicemail", "call", "text"}:
        raise GrasshopperError("Webhook payload type must be voicemail, call, or text.")

    phone_number = payload.get("phone_number")
    if not phone_number:
        raise GrasshopperError("Webhook payload requires phone_number.")

    message_id = payload.get("message_id") or (
        f"webhook:{event_type}:{phone_number}:{payload.get('received_at', datetime.utcnow().isoformat())}"
    )

    received_at_raw = payload.get("received_at")
    if isinstance(received_at_raw, str):
        received_at = datetime.fromisoformat(received_at_raw.replace("Z", "+00:00")).replace(tzinfo=None)
    else:
        received_at = datetime.utcnow()

    event = ParsedGrasshopperEvent(
        event_type=event_type,
        message_id=message_id,
        phone_number=phone_number,
        contact_name=payload.get("contact_name"),
        body=payload.get("body"),
        transcript=payload.get("transcript"),
        duration_seconds=payload.get("duration_seconds"),
        received_at=received_at,
        audio_filename=None,
        audio_bytes=None,
    )

    imported_as = import_grasshopper_event(db, event)
    db.commit()

    return {
        "imported": imported_as is not None,
        "type": imported_as,
        "message_id": message_id,
    }
