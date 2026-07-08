import email
import imaplib
from datetime import datetime, timedelta
from email.message import Message

from app.services.grasshopper_parser import is_grasshopper_email, parse_grasshopper_email
from app.services.mailbox_config import MailboxConfig, get_grasshopper_mailbox


class GrasshopperError(Exception):
    pass


def fetch_grasshopper_emails(since_days: int = 30) -> list[Message]:
    mailbox = get_grasshopper_mailbox()
    if not mailbox:
        raise GrasshopperError(
            "Grasshopper IMAP is not configured. Set GRASSHOPPER_IMAP_* or WORK_EMAIL_IMAP_* "
            "(Outlook) in organizer/backend/.env."
        )

    return _fetch_messages(mailbox, since_days)


def _fetch_messages(mailbox: MailboxConfig, since_days: int) -> list[Message]:
    since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
    messages: list[Message] = []

    try:
        connection = imaplib.IMAP4_SSL(mailbox.host, mailbox.port)
        connection.login(mailbox.user, mailbox.password)
        connection.select(mailbox.folder)

        status, data = connection.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            raise GrasshopperError("Could not search the Grasshopper inbox.")

        for num in data[0].split():
            if not num:
                continue
            fetch_status, fetched = connection.fetch(num, "(RFC822)")
            if fetch_status != "OK" or not fetched or not fetched[0]:
                continue
            raw_email = fetched[0][1]
            if not isinstance(raw_email, bytes):
                continue
            message = email.message_from_bytes(raw_email)
            if is_grasshopper_email(message):
                messages.append(message)

        connection.logout()
    except imaplib.IMAP4.error as exc:
        raise GrasshopperError(f"IMAP connection failed: {exc}") from exc

    return messages


def parse_grasshopper_messages(messages: list[Message]) -> list:
    from app.services.grasshopper_parser import ParsedGrasshopperEvent

    events: list[ParsedGrasshopperEvent] = []
    for message in messages:
        event = parse_grasshopper_email(message)
        if event:
            events.append(event)
    return events
