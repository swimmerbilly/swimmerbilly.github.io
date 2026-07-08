from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Project, Voicemail
from app.schemas import VoicemailCreate, VoicemailRead, VoicemailUpdate
from app.services.comm_serializer import to_voicemail_read

router = APIRouter(prefix="/voicemails", tags=["voicemails"])


@router.get("", response_model=list[VoicemailRead])
def list_voicemails(
    project_id: int | None = Query(default=None),
    unlistened_only: bool = Query(default=False),
    unlinked_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[VoicemailRead]:
    query = db.query(Voicemail).options(joinedload(Voicemail.project))
    if project_id is not None:
        query = query.filter(Voicemail.project_id == project_id)
    if unlistened_only:
        query = query.filter(Voicemail.is_listened.is_(False))
    if unlinked_only:
        query = query.filter(Voicemail.project_id.is_(None))
    voicemails = query.order_by(Voicemail.received_at.desc()).all()
    return [to_voicemail_read(vm) for vm in voicemails]


@router.post("", response_model=VoicemailRead, status_code=status.HTTP_201_CREATED)
def create_voicemail(payload: VoicemailCreate, db: Session = Depends(get_db)) -> VoicemailRead:
    voicemail = Voicemail(**payload.model_dump())
    db.add(voicemail)
    db.commit()
    db.refresh(voicemail)
    if voicemail.project_id:
        voicemail.project = db.get(Project, voicemail.project_id)
    return to_voicemail_read(voicemail)


@router.get("/{voicemail_id}", response_model=VoicemailRead)
def get_voicemail(voicemail_id: int, db: Session = Depends(get_db)) -> VoicemailRead:
    voicemail = (
        db.query(Voicemail)
        .options(joinedload(Voicemail.project))
        .filter(Voicemail.id == voicemail_id)
        .one_or_none()
    )
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    return to_voicemail_read(voicemail)


@router.patch("/{voicemail_id}", response_model=VoicemailRead)
def update_voicemail(
    voicemail_id: int, payload: VoicemailUpdate, db: Session = Depends(get_db)
) -> VoicemailRead:
    voicemail = (
        db.query(Voicemail)
        .options(joinedload(Voicemail.project))
        .filter(Voicemail.id == voicemail_id)
        .one_or_none()
    )
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voicemail, field, value)

    db.commit()
    db.refresh(voicemail)
    if voicemail.project_id and not voicemail.project:
        voicemail.project = db.get(Project, voicemail.project_id)
    return to_voicemail_read(voicemail)


@router.delete("/{voicemail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voicemail(voicemail_id: int, db: Session = Depends(get_db)) -> None:
    voicemail = db.get(Voicemail, voicemail_id)
    if not voicemail:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    db.delete(voicemail)
    db.commit()
