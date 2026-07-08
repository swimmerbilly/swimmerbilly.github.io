from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import HarvestStatus, HarvestSyncResult
from app.services.harvest import HarvestClient, HarvestError
from app.services.harvest_sync import sync_projects_from_harvest

router = APIRouter(prefix="/harvest", tags=["harvest"])


@router.get("/status", response_model=HarvestStatus)
async def harvest_status() -> HarvestStatus:
    if not settings.harvest_configured:
        return HarvestStatus(configured=False)

    client = HarvestClient()
    try:
        me = await client.get_me()
    except HarvestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return HarvestStatus(
        configured=True,
        account_id=settings.harvest_account_id,
        user_name=f"{me.get('first_name', '')} {me.get('last_name', '')}".strip() or me.get("email"),
    )


@router.post("/sync", response_model=HarvestSyncResult)
async def harvest_sync(db: Session = Depends(get_db)) -> HarvestSyncResult:
    try:
        result = await sync_projects_from_harvest(db)
    except HarvestError as exc:
        status_code = exc.status_code or 400
        if status_code == 401:
            status_code = 401
        elif status_code == 403:
            status_code = 403
        else:
            status_code = 400 if status_code < 500 else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return HarvestSyncResult(**result)
