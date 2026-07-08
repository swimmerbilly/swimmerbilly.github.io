import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.services.mailbox_config import get_grasshopper_mailbox
from app.database import get_db
from app.schemas import GrasshopperStatus, GrasshopperSyncResult, GrasshopperWebhookEvent
from app.services.grasshopper_imap import GrasshopperError
from app.services.grasshopper_sync import import_grasshopper_webhook_event, sync_grasshopper_from_imap

router = APIRouter(prefix="/grasshopper", tags=["grasshopper"])


@router.get("/status", response_model=GrasshopperStatus)
def grasshopper_status() -> GrasshopperStatus:
    mailbox = get_grasshopper_mailbox()
    imap_configured = mailbox is not None
    return GrasshopperStatus(
        configured=imap_configured or settings.grasshopper_webhook_configured,
        imap_configured=imap_configured,
        webhook_configured=settings.grasshopper_webhook_configured,
        imap_host=mailbox.host if mailbox else settings.grasshopper_imap_host,
        imap_user=mailbox.user if mailbox else settings.grasshopper_imap_user,
        imap_folder=mailbox.folder if mailbox else settings.grasshopper_imap_folder,
        webhook_url_hint="/api/grasshopper/webhook" if settings.grasshopper_webhook_configured else None,
        uses_work_outlook=imap_configured and not settings.grasshopper_imap_configured,
    )


@router.post("/sync", response_model=GrasshopperSyncResult)
async def grasshopper_sync(
    since_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> GrasshopperSyncResult:
    try:
        result = await asyncio.to_thread(sync_grasshopper_from_imap, db, since_days)
    except GrasshopperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GrasshopperSyncResult(**result)


@router.post("/webhook")
def grasshopper_webhook(
    payload: GrasshopperWebhookEvent,
    db: Session = Depends(get_db),
    x_grasshopper_secret: str | None = Header(default=None),
) -> dict:
    if not settings.grasshopper_webhook_configured:
        raise HTTPException(
            status_code=400,
            detail="Grasshopper webhook is not configured. Set GRASSHOPPER_WEBHOOK_SECRET.",
        )
    if x_grasshopper_secret != settings.grasshopper_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid Grasshopper webhook secret.")

    try:
        result = import_grasshopper_webhook_event(db, payload.model_dump())
    except GrasshopperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result
