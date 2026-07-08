from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LinkCommRequest, LinkSuggestion, ProjectSuggestion
from app.services.project_linking import link_comm_to_project, suggest_project_for_comm, suggest_unlinked_comms

router = APIRouter(prefix="/linking", tags=["linking"])


@router.get("/suggest", response_model=list[ProjectSuggestion])
def suggest_link(
    comm_type: str = Query(pattern=r"^(email|text|voicemail|call)$"),
    comm_id: int = Query(ge=1),
    db: Session = Depends(get_db),
) -> list[ProjectSuggestion]:
    return suggest_project_for_comm(db, comm_type, comm_id)


@router.get("/unlinked", response_model=list[LinkSuggestion])
def list_unlinked_suggestions(db: Session = Depends(get_db)) -> list[LinkSuggestion]:
    return suggest_unlinked_comms(db)


@router.post("/apply")
def apply_link(payload: LinkCommRequest, db: Session = Depends(get_db)) -> dict:
    ok = link_comm_to_project(db, payload.comm_type, payload.comm_id, payload.project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Communication or project not found")
    return {"success": True}
