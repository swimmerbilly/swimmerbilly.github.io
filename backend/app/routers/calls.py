from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Call, CommunicationDirection, Project
from app.schemas import CallCreate, CallRead, CallUpdate, QuickCallNoteCreate
from app.services.call_serializer import to_call_read

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=list[CallRead])
def list_calls(
    project_id: int | None = Query(default=None),
    unlinked_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[CallRead]:
    query = db.query(Call).options(joinedload(Call.project))
    if project_id is not None:
        query = query.filter(Call.project_id == project_id)
    if unlinked_only:
        query = query.filter(Call.project_id.is_(None))
    calls = query.order_by(Call.called_at.desc()).all()
    return [to_call_read(call) for call in calls]


@router.post("/quick-note", response_model=CallRead, status_code=status.HTTP_201_CREATED)
def create_quick_call_note(payload: QuickCallNoteCreate, db: Session = Depends(get_db)) -> CallRead:
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    follow_up_at = None
    if payload.follow_up_days:
        follow_up_at = datetime.utcnow() + timedelta(days=payload.follow_up_days)

    call = Call(
        project_id=payload.project_id,
        direction=CommunicationDirection.INBOUND,
        contact_name=payload.contact_name.strip(),
        caller_role=payload.caller_role.value if payload.caller_role else None,
        phone_number=payload.phone_number.strip() if payload.phone_number else "—",
        notes=payload.notes.strip(),
        duration_seconds=None,
        follow_up_at=follow_up_at,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    call.project = project
    return to_call_read(call)


@router.post("", response_model=CallRead, status_code=status.HTTP_201_CREATED)
def create_call(payload: CallCreate, db: Session = Depends(get_db)) -> CallRead:
    data = payload.model_dump()
    if data.get("caller_role") is not None:
        data["caller_role"] = data["caller_role"].value
    call = Call(**data)
    db.add(call)
    db.commit()
    db.refresh(call)
    if call.project_id:
        call.project = db.get(Project, call.project_id)
    return to_call_read(call)


@router.get("/{call_id}", response_model=CallRead)
def get_call(call_id: int, db: Session = Depends(get_db)) -> CallRead:
    call = db.query(Call).options(joinedload(Call.project)).filter(Call.id == call_id).one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return to_call_read(call)


@router.patch("/{call_id}", response_model=CallRead)
def update_call(
    call_id: int, payload: CallUpdate, db: Session = Depends(get_db)
) -> CallRead:
    call = db.query(Call).options(joinedload(Call.project)).filter(Call.id == call_id).one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "caller_role" and value is not None:
            value = value.value
        setattr(call, field, value)

    if call.project_id and not call.project:
        call.project = db.get(Project, call.project_id)

    db.commit()
    db.refresh(call)
    return to_call_read(call)


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: int, db: Session = Depends(get_db)) -> None:
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.delete(call)
    db.commit()
