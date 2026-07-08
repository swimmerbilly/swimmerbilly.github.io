from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Email, Project
from app.schemas import EmailCreate, EmailRead, EmailUpdate
from app.services.comm_serializer import to_email_read

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=list[EmailRead])
def list_emails(
    project_id: int | None = Query(default=None),
    unread_only: bool = Query(default=False),
    unlinked_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[EmailRead]:
    query = db.query(Email).options(joinedload(Email.project))
    if project_id is not None:
        query = query.filter(Email.project_id == project_id)
    if unread_only:
        query = query.filter(Email.is_read.is_(False))
    if unlinked_only:
        query = query.filter(Email.project_id.is_(None))
    emails = query.order_by(Email.received_at.desc()).all()
    return [to_email_read(email) for email in emails]


@router.post("", response_model=EmailRead, status_code=status.HTTP_201_CREATED)
def create_email(payload: EmailCreate, db: Session = Depends(get_db)) -> EmailRead:
    email = Email(**payload.model_dump())
    db.add(email)
    db.commit()
    db.refresh(email)
    if email.project_id:
        email.project = db.get(Project, email.project_id)
    return to_email_read(email)


@router.get("/{email_id}", response_model=EmailRead)
def get_email(email_id: int, db: Session = Depends(get_db)) -> EmailRead:
    email = db.query(Email).options(joinedload(Email.project)).filter(Email.id == email_id).one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return to_email_read(email)


@router.patch("/{email_id}", response_model=EmailRead)
def update_email(
    email_id: int, payload: EmailUpdate, db: Session = Depends(get_db)
) -> EmailRead:
    email = db.query(Email).options(joinedload(Email.project)).filter(Email.id == email_id).one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(email, field, value)

    db.commit()
    db.refresh(email)
    if email.project_id and not email.project:
        email.project = db.get(Project, email.project_id)
    return to_email_read(email)


@router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(email_id: int, db: Session = Depends(get_db)) -> None:
    email = db.get(Email, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    db.delete(email)
    db.commit()
