from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AttentionItem
from app.services.attention import build_attention_queue

router = APIRouter(prefix="/attention", tags=["attention"])


@router.get("", response_model=list[AttentionItem])
def get_attention_queue(db: Session = Depends(get_db)) -> list[AttentionItem]:
    return build_attention_queue(db)
