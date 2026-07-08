from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TextMessage
from app.schemas import TextCreate, TextRead, TextUpdate

router = APIRouter(prefix="/texts", tags=["texts"])


@router.get("", response_model=list[TextRead])
def list_texts(
    project_id: int | None = Query(default=None),
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[TextMessage]:
    query = db.query(TextMessage)
    if project_id is not None:
        query = query.filter(TextMessage.project_id == project_id)
    if unread_only:
        query = query.filter(TextMessage.is_read.is_(False))
    return query.order_by(TextMessage.sent_at.desc()).all()


@router.post("", response_model=TextRead, status_code=status.HTTP_201_CREATED)
def create_text(payload: TextCreate, db: Session = Depends(get_db)) -> TextMessage:
    text = TextMessage(**payload.model_dump())
    db.add(text)
    db.commit()
    db.refresh(text)
    return text


@router.get("/{text_id}", response_model=TextRead)
def get_text(text_id: int, db: Session = Depends(get_db)) -> TextMessage:
    text = db.get(TextMessage, text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text


@router.patch("/{text_id}", response_model=TextRead)
def update_text(
    text_id: int, payload: TextUpdate, db: Session = Depends(get_db)
) -> TextMessage:
    text = db.get(TextMessage, text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(text, field, value)

    db.commit()
    db.refresh(text)
    return text


@router.delete("/{text_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_text(text_id: int, db: Session = Depends(get_db)) -> None:
    text = db.get(TextMessage, text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    db.delete(text)
    db.commit()
