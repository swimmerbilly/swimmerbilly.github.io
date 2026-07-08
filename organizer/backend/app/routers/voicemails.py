from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Voicemail
from app.schemas import VoicemailCreate, VoicemailRead, VoicemailUpdate

router = APIRouter(prefix="/voicemails", tags=["voicemails"])


@router.get("", response_model=list[VoicemailRead])
def list_voicemails(
    project_id: int | None = Query(default=None),
    unlistened_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[Voicemail]:
    query = db.query(Voicemail)
    if project_id is not None:
        query = query.filter(Voicemail.project_id == project_id)
    if unlistened_only:
        query = query.filter(Voicemail.is_listened.is_(False))
    return query.order_by(Voicemail.received_at.desc()).all()


@router.post("", response_model=VoicemailRead, status_code=status.HTTP_201_CREATED)
def create_voicemail(payload: VoicemailCreate, db: Session = Depends(get_db)) -> Voicemail:
    voicemail = Voicemail(**payload.model_dump())
    db.add(voicemail)
    db.commit()
    db.refresh(voicemail)
    return voicemail


@router.get("/{voicemail_id}", response_model=VoicemailRead)
def get_voicemail(voicemail_id: int, db: Session = Depends(get_db)) -> Voicemail:
    voicemail = db.get(Voicemail, voicemail_id)
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    return voicemail


@router.patch("/{voicemail_id}", response_model=VoicemailRead)
def update_voicemail(
    voicemail_id: int, payload: VoicemailUpdate, db: Session = Depends(get_db)
) -> Voicemail:
    voicemail = db.get(Voicemail, voicemail_id)
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voicemail, field, value)

    db.commit()
    db.refresh(voicemail)
    return voicemail


@router.delete("/{voicemail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voicemail(voicemail_id: int, db: Session = Depends(get_db)) -> None:
    voicemail = db.get(Voicemail, voicemail_id)
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    db.delete(voicemail)
    db.commit()
