from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SetupStatus, SetupStepSave
from app.services.settings_store import (
    STEP_DEFAULTS,
    STEP_FIELD_MAP,
    build_setup_status,
    load_settings_from_db,
    save_settings,
)

router = APIRouter(prefix="/setup", tags=["setup"])


@router.get("", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    load_settings_from_db(db)
    return build_setup_status(db)


@router.put("/{step_id}", response_model=SetupStatus)
def save_setup_step(
    step_id: str,
    payload: SetupStepSave,
    db: Session = Depends(get_db),
) -> SetupStatus:
    if step_id not in STEP_FIELD_MAP:
        raise HTTPException(status_code=404, detail="Unknown setup step")

    data = {**STEP_DEFAULTS.get(step_id, {}), **payload.values}
    save_settings(db, data)
    load_settings_from_db(db)
    return build_setup_status(db)
