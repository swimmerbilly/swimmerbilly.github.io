import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MailboxStatus, MailboxSyncResult
from app.services.email_imap import MailboxError
from app.services.email_sync import get_mailbox_status, sync_all_mailboxes, sync_mailbox
from app.services.mailbox_config import get_personal_mailbox, get_work_mailbox

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


@router.get("/status", response_model=list[MailboxStatus])
def mailbox_status() -> list[MailboxStatus]:
    return [MailboxStatus(**item) for item in get_mailbox_status()]


@router.post("/sync", response_model=MailboxSyncResult)
async def sync_mailboxes(
    account: str | None = Query(default=None, pattern="^(work|personal)$"),
    since_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> MailboxSyncResult:
    try:
        if account == "work":
            mailbox = get_work_mailbox()
            if not mailbox:
                raise MailboxError("Work Outlook mailbox is not configured.")
            result = await asyncio.to_thread(sync_mailbox, db, mailbox, since_days)
            return MailboxSyncResult(accounts_synced=1, results=[result], created=result["created"], skipped=result["skipped"])
        if account == "personal":
            mailbox = get_personal_mailbox()
            if not mailbox:
                raise MailboxError("Personal Gmail mailbox is not configured.")
            result = await asyncio.to_thread(sync_mailbox, db, mailbox, since_days)
            return MailboxSyncResult(accounts_synced=1, results=[result], created=result["created"], skipped=result["skipped"])

        payload = await asyncio.to_thread(sync_all_mailboxes, db, since_days)
    except MailboxError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MailboxSyncResult(**payload)
