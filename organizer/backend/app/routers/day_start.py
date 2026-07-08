from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChecklistItemCreate, ChecklistItemRead, ChecklistItemUpdate, DayPlanRead
from app.services.assistant import AssistantError
from app.services.day_start_service import (
    add_checklist_item,
    delete_checklist_item,
    generate_day_plan,
    generate_weekly_review_plan,
    generate_wrap_up_plan,
    get_day_plan,
    toggle_checklist_item,
)

router = APIRouter(prefix="/day-start", tags=["day-start"])


def _to_read(plan) -> DayPlanRead:
    return DayPlanRead.from_model(plan)


@router.get("", response_model=DayPlanRead | None)
def read_day_plan(
    plan_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DayPlanRead | None:
    plan = get_day_plan(db, plan_date)
    return _to_read(plan) if plan else None


@router.post("/generate", response_model=DayPlanRead)
async def create_day_plan(
    regenerate: bool = Query(default=False),
    plan_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DayPlanRead:
    try:
        plan = await generate_day_plan(db, plan_date, regenerate=regenerate)
    except AssistantError as exc:
        status_code = exc.status_code or 400
        if status_code >= 500:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return _to_read(plan)


@router.post("/wrap-up", response_model=DayPlanRead)
async def create_wrap_up(
    plan_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DayPlanRead:
    try:
        plan = await generate_wrap_up_plan(db, plan_date)
    except AssistantError as exc:
        status_code = exc.status_code or 400
        if status_code >= 500:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return _to_read(plan)


@router.post("/weekly-review", response_model=DayPlanRead)
async def create_weekly_review(
    plan_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DayPlanRead:
    try:
        plan = await generate_weekly_review_plan(db, plan_date)
    except AssistantError as exc:
        status_code = exc.status_code or 400
        if status_code >= 500:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return _to_read(plan)


@router.post("/checklist", response_model=ChecklistItemRead, status_code=201)
def create_checklist_item(
    payload: ChecklistItemCreate,
    plan_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
) -> ChecklistItemRead:
    try:
        item = add_checklist_item(db, payload.text, plan_date)
    except AssistantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return item


@router.patch("/checklist/{item_id}", response_model=ChecklistItemRead)
def update_checklist_item(
    item_id: int,
    payload: ChecklistItemUpdate,
    db: Session = Depends(get_db),
) -> ChecklistItemRead:
    try:
        item = toggle_checklist_item(db, item_id, payload.is_completed)
    except AssistantError as exc:
        raise HTTPException(status_code=exc.status_code or 404, detail=str(exc)) from exc
    return item


@router.delete("/checklist/{item_id}", status_code=204)
def remove_checklist_item(item_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_checklist_item(db, item_id)
    except AssistantError as exc:
        raise HTTPException(status_code=exc.status_code or 404, detail=str(exc)) from exc
