from sqlalchemy.orm import Session

from app.models import CommunicationDirection, Email
from app.services.email_imap import MailboxError, fetch_mailbox_messages, parse_mailbox_email
from app.services.mailbox_config import MailboxConfig, get_personal_mailbox, get_work_mailbox, list_configured_mailboxes


def sync_mailbox(db: Session, mailbox: MailboxConfig, since_days: int = 30) -> dict:
    messages = fetch_mailbox_messages(mailbox, since_days=since_days)
    created = 0
    skipped = 0

    for message in messages:
        parsed = parse_mailbox_email(message, mailbox.label, mailbox.user)
        if not parsed:
            skipped += 1
            continue

        existing = (
            db.query(Email).filter(Email.external_message_id == parsed.message_id).one_or_none()
        )
        if existing:
            skipped += 1
            continue

        db.add(
            Email(
                project_id=None,
                direction=CommunicationDirection.INBOUND,
                from_address=parsed.from_address,
                to_address=parsed.to_address,
                subject=parsed.subject,
                body=parsed.body,
                is_read=False,
                is_starred=False,
                account_label=parsed.account_label,
                external_message_id=parsed.message_id,
                received_at=parsed.received_at,
            )
        )
        created += 1

    db.commit()
    return {
        "account": mailbox.label,
        "messages_scanned": len(messages),
        "created": created,
        "skipped": skipped,
    }


def sync_all_mailboxes(db: Session, since_days: int = 30) -> dict:
    mailboxes = list_configured_mailboxes()
    if not mailboxes:
        raise MailboxError(
            "No email accounts configured. Set WORK_EMAIL_IMAP_* (Outlook) and/or "
            "PERSONAL_EMAIL_IMAP_* (Gmail) in organizer/backend/.env."
        )

    results = [sync_mailbox(db, mailbox, since_days) for mailbox in mailboxes]
    return {
        "accounts_synced": len(results),
        "results": results,
        "created": sum(item["created"] for item in results),
        "skipped": sum(item["skipped"] for item in results),
    }


def get_mailbox_status() -> list[dict]:
    status: list[dict] = []
    work = get_work_mailbox()
    personal = get_personal_mailbox()

    if work:
        status.append(
            {
                "label": "work",
                "provider": "outlook",
                "configured": True,
                "host": work.host,
                "user": work.user,
                "folder": work.folder,
            }
        )
    else:
        status.append({"label": "work", "provider": "outlook", "configured": False})

    if personal:
        status.append(
            {
                "label": "personal",
                "provider": "gmail",
                "configured": True,
                "host": personal.host,
                "user": personal.user,
                "folder": personal.folder,
            }
        )
    else:
        status.append({"label": "personal", "provider": "gmail", "configured": False})

    return status
