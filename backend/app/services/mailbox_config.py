from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class MailboxConfig:
    label: str
    host: str
    port: int
    user: str
    password: str
    folder: str = "INBOX"


def get_work_mailbox() -> MailboxConfig | None:
    if not all(
        [
            settings.work_email_imap_host,
            settings.work_email_imap_user,
            settings.work_email_imap_password,
        ]
    ):
        return None
    return MailboxConfig(
        label="work",
        host=settings.work_email_imap_host,
        port=settings.work_email_imap_port,
        user=settings.work_email_imap_user,
        password=settings.work_email_imap_password,
        folder=settings.work_email_imap_folder,
    )


def get_personal_mailbox() -> MailboxConfig | None:
    if not all(
        [
            settings.personal_email_imap_host,
            settings.personal_email_imap_user,
            settings.personal_email_imap_password,
        ]
    ):
        return None
    return MailboxConfig(
        label="personal",
        host=settings.personal_email_imap_host,
        port=settings.personal_email_imap_port,
        user=settings.personal_email_imap_user,
        password=settings.personal_email_imap_password,
        folder=settings.personal_email_imap_folder,
    )


def get_grasshopper_mailbox() -> MailboxConfig | None:
    if settings.grasshopper_imap_configured:
        return MailboxConfig(
            label="grasshopper",
            host=settings.grasshopper_imap_host or "",
            port=settings.grasshopper_imap_port,
            user=settings.grasshopper_imap_user or "",
            password=settings.grasshopper_imap_password or "",
            folder=settings.grasshopper_imap_folder,
        )
    work = get_work_mailbox()
    if work:
        return MailboxConfig(
            label="grasshopper",
            host=work.host,
            port=work.port,
            user=work.user,
            password=work.password,
            folder=work.folder,
        )
    return None


def list_configured_mailboxes() -> list[MailboxConfig]:
    mailboxes: list[MailboxConfig] = []
    work = get_work_mailbox()
    personal = get_personal_mailbox()
    if work:
        mailboxes.append(work)
    if personal:
        mailboxes.append(personal)
    return mailboxes
