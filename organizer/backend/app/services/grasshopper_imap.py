import email
import imaplib
from datetime import datetime, timedelta
from email.message import Message
from pathlib import Path

from app.config import settings
from app.services.grasshopper_parser import ParsedGrasshopperEvent, is_grasshopper_email, parse_grasshopper_email


class GrasshopperError(Exception):
    pass


def fetch_grasshopper_emails(since_days: int = 30) -> list[Message]:
    if not settings.grasshopper_imap_configured:
        raise GrasshopperError(
            "Grasshopper IMAP is not configured. Set GRASSHOPPER_IMAP_HOST, "
            "GRASSHOPPER_IMAP_USER, and GRASSHOPPER_IMAP_PASSWORD."
        )

    since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
    messages: list[Message] = []

    try:
        mailbox = imaplib.IMAP4_SSL(settings.grasshopper_imap_host, settings.grasshopper_imap_port)
        mailbox.login(settings.grasshopper_imap_user, settings.grasshopper_imap_password)
        mailbox.select(settings.grasshopper_imap_folder)

        status, data = mailbox.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            raise GrasshopperError("Could not search the Grasshopper inbox.")

        for num in data[0].split():
            if not num:
                continue
            fetch_status, fetched = mailbox.fetch(num, "(RFC822)")
            if fetch_status != "OK" or not fetched or not fetched[0]:
                continue
            raw_email = fetched[0][1]
            if not isinstance(raw_email, bytes):
                continue
            message = email.message_from_bytes(raw_email)
            if is_grasshopper_email(message):
                messages.append(message)

        mailbox.logout()
    except imaplib.IMAP4.error as exc:
        raise GrasshopperError(f"IMAP connection failed: {exc}") from exc

    return messages


def parse_grasshopper_messages(messages: list[Message]) -> list[ParsedGrasshopperEvent]:
    events: list[ParsedGrasshopperEvent] = []
    for message in messages:
        event = parse_grasshopper_email(message)
        if event:
            events.append(event)
    return events
