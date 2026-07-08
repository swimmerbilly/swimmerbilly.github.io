import email
import imaplib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime, parseaddr

from app.services.grasshopper_parser import is_grasshopper_email
from app.services.mailbox_config import MailboxConfig


class MailboxError(Exception):
    pass


@dataclass
class ParsedMailboxEmail:
    message_id: str
    from_address: str
    to_address: str
    subject: str
    body: str
    received_at: datetime
    account_label: str


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


def _message_datetime(message: Message) -> datetime:
    date_header = message.get("Date")
    if date_header:
        try:
            return parsedate_to_datetime(date_header).replace(tzinfo=None)
        except (TypeError, ValueError, IndexError):
            pass
    return datetime.utcnow()


def _extract_address(header_value: str | None) -> str:
    if not header_value:
        return ""
    name, addr = parseaddr(header_value)
    return addr or name or header_value


def _message_body_text(message: Message) -> str:
    if message.is_multipart():
        plain_body = ""
        html_body = ""
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not isinstance(payload, bytes):
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace").strip()
            if content_type == "text/plain" and not plain_body:
                plain_body = text
            elif content_type == "text/html" and not html_body:
                html_body = re.sub(r"<[^>]+>", " ", text)
                html_body = re.sub(r"\s+", " ", html_body).strip()
        return plain_body or html_body

    payload = message.get_payload(decode=True)
    if isinstance(payload, bytes):
        charset = message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace").strip()
    if isinstance(payload, str):
        return payload.strip()
    return ""


def parse_mailbox_email(message: Message, account_label: str, mailbox_user: str) -> ParsedMailboxEmail | None:
    if is_grasshopper_email(message):
        return None

    message_id = message.get("Message-ID") or (
        f"{account_label}:{message.get('Subject')}:{_message_datetime(message).isoformat()}"
    )
    from_address = _extract_address(message.get("From"))
    to_header = message.get("To") or message.get("Delivered-To") or mailbox_user
    to_addresses = [addr for _, addr in getaddresses([to_header]) if addr]
    to_address = ", ".join(to_addresses) if to_addresses else mailbox_user

    return ParsedMailboxEmail(
        message_id=message_id,
        from_address=from_address or "unknown",
        to_address=to_address,
        subject=_decode_header_value(message.get("Subject"))[:500],
        body=_message_body_text(message)[:20000],
        received_at=_message_datetime(message),
        account_label=account_label,
    )


def fetch_mailbox_messages(mailbox: MailboxConfig, since_days: int = 30) -> list[Message]:
    since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
    messages: list[Message] = []

    try:
        connection = imaplib.IMAP4_SSL(mailbox.host, mailbox.port)
        connection.login(mailbox.user, mailbox.password)
        connection.select(mailbox.folder)

        status, data = connection.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            raise MailboxError(f"Could not search {mailbox.label} inbox.")

        for num in data[0].split():
            if not num:
                continue
            fetch_status, fetched = connection.fetch(num, "(RFC822)")
            if fetch_status != "OK" or not fetched or not fetched[0]:
                continue
            raw_email = fetched[0][1]
            if not isinstance(raw_email, bytes):
                continue
            messages.append(email.message_from_bytes(raw_email))

        connection.logout()
    except imaplib.IMAP4.error as exc:
        raise MailboxError(f"{mailbox.label} IMAP connection failed: {exc}") from exc

    return messages
