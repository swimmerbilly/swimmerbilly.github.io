import re
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime

PHONE_PATTERN = re.compile(
    r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"
)


@dataclass
class ParsedGrasshopperEvent:
    event_type: str
    message_id: str
    phone_number: str
    contact_name: str | None
    body: str | None
    transcript: str | None
    duration_seconds: int | None
    received_at: datetime
    audio_filename: str | None
    audio_bytes: bytes | None


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for chunk, encoding in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(encoding or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def _extract_phone_number(*sources: str | None) -> str | None:
    for source in sources:
        if not source:
            continue
        match = PHONE_PATTERN.search(source)
        if match:
            return match.group(0)
    return None


def _extract_contact_name(subject: str) -> str | None:
    lowered = subject.lower()
    for prefix in ("voicemail from", "voice message from", "missed call from", "text from", "sms from"):
        if prefix in lowered:
            remainder = subject[lowered.index(prefix) + len(prefix) :].strip(" -:")
            phone = _extract_phone_number(remainder)
            if phone:
                name = remainder.replace(phone, "").strip(" -()")
                return name or None
            return remainder or None
    return None


def _message_datetime(message: Message) -> datetime:
    date_header = message.get("Date")
    if date_header:
        try:
            return parsedate_to_datetime(date_header).replace(tzinfo=None)
        except (TypeError, ValueError, IndexError):
            pass
    return datetime.utcnow()


def _message_body_text(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and part.get_content_disposition() != "attachment":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace").strip()
        return ""

    payload = message.get_payload(decode=True)
    if isinstance(payload, bytes):
        charset = message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace").strip()
    if isinstance(payload, str):
        return payload.strip()
    return ""


def _audio_attachment(message: Message) -> tuple[str | None, bytes | None]:
    if not message.is_multipart():
        return None, None

    for part in message.walk():
        if part.get_content_disposition() != "attachment":
            continue
        filename = part.get_filename()
        content_type = part.get_content_type()
        if not filename and content_type not in {"audio/mpeg", "audio/wav", "audio/x-wav"}:
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            continue
        safe_name = filename or "voicemail.mp3"
        return safe_name, payload
    return None, None


def is_grasshopper_email(message: Message) -> bool:
    subject = _decode_header_value(message.get("Subject")).lower()
    sender = _decode_header_value(message.get("From")).lower()

    if "grasshopper" in sender:
        return True

    grasshopper_subject_markers = (
        "voicemail from",
        "voice message",
        "missed call from",
        "new text message",
        "text message from",
        "sms from",
    )
    return any(marker in subject for marker in grasshopper_subject_markers)


def parse_grasshopper_email(message: Message) -> ParsedGrasshopperEvent | None:
    if not is_grasshopper_email(message):
        return None

    subject = _decode_header_value(message.get("Subject"))
    subject_lower = subject.lower()
    body = _message_body_text(message)
    message_id = message.get("Message-ID") or f"{subject}:{_message_datetime(message).isoformat()}"
    phone_number = _extract_phone_number(subject, body) or "unknown"
    contact_name = _extract_contact_name(subject)
    received_at = _message_datetime(message)
    audio_filename, audio_bytes = _audio_attachment(message)

    if "voicemail" in subject_lower or "voice message" in subject_lower:
        transcript = body or None
        return ParsedGrasshopperEvent(
            event_type="voicemail",
            message_id=message_id,
            phone_number=phone_number,
            contact_name=contact_name,
            body=None,
            transcript=transcript,
            duration_seconds=None,
            received_at=received_at,
            audio_filename=audio_filename,
            audio_bytes=audio_bytes,
        )

    if "missed call" in subject_lower:
        return ParsedGrasshopperEvent(
            event_type="call",
            message_id=message_id,
            phone_number=phone_number,
            contact_name=contact_name,
            body=body or "Missed call from Grasshopper",
            transcript=None,
            duration_seconds=0,
            received_at=received_at,
            audio_filename=None,
            audio_bytes=None,
        )

    if "text" in subject_lower or "sms" in subject_lower:
        return ParsedGrasshopperEvent(
            event_type="text",
            message_id=message_id,
            phone_number=phone_number,
            contact_name=contact_name,
            body=body or subject,
            transcript=None,
            duration_seconds=None,
            received_at=received_at,
            audio_filename=None,
            audio_bytes=None,
        )

    if audio_filename and audio_bytes:
        return ParsedGrasshopperEvent(
            event_type="voicemail",
            message_id=message_id,
            phone_number=phone_number,
            contact_name=contact_name,
            body=None,
            transcript=body or None,
            duration_seconds=None,
            received_at=received_at,
            audio_filename=audio_filename,
            audio_bytes=audio_bytes,
        )

    return None
