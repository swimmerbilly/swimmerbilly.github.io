from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Call
from app.schemas import CallCreate, CallRead, CallUpdate

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=list[CallRead])
def list_calls(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Call]:
    query = db.query(Call)
    if project_id is not None:
        query = query.filter(Call.project_id == project_id)
    return query.order_by(Call.called_at.desc()).all()


@router.post("", response_model=CallRead, status_code=status.HTTP_201_CREATED)
def create_call(payload: CallCreate, db: Session = Depends(get_db)) -> Call:
    call = Call(**payload.model_dump())
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@router.get("/{call_id}", response_model=CallRead)
def get_call(call_id: int, db: Session = Depends(get_db)) -> Call:
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.patch("/{call_id}", response_model=CallRead)
def update_call(
    call_id: int, payload: CallUpdate, db: Session = Depends(get_db)
) -> Call:
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(call, field, value)

    db.commit()
    db.refresh(call)
    return call


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: int, db: Session = Depends(get_db)) -> None:
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.delete(call)
    db.commit()
