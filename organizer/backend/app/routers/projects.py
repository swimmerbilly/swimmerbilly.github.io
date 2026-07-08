from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Call, Project
from app.schemas import CallRead, ProjectContact, ProjectCreate, ProjectRead, ProjectUpdate, TimelineEntry
from app.services.project_contacts import build_project_contacts
from app.services.project_timeline import build_project_timeline
from app.services.call_serializer import to_call_read

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.updated_at.desc()).all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/timeline", response_model=list[TimelineEntry])
def get_project_timeline(project_id: int, db: Session = Depends(get_db)) -> list[TimelineEntry]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_project_timeline(db, project_id)


@router.get("/{project_id}/contacts", response_model=list[ProjectContact])
def get_project_contacts(project_id: int, db: Session = Depends(get_db)) -> list[ProjectContact]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_project_contacts(db, project_id)


@router.get("/{project_id}/calls", response_model=list[CallRead])
def get_project_calls(project_id: int, db: Session = Depends(get_db)) -> list[CallRead]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    calls = (
        db.query(Call)
        .options(joinedload(Call.project))
        .filter(Call.project_id == project_id)
        .order_by(Call.called_at.desc())
        .all()
    )
    return [to_call_read(call) for call in calls]


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)
) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.harvest_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Harvest-synced projects cannot be deleted locally. Archive them in Harvest instead.",
        )
    db.delete(project)
    db.commit()
