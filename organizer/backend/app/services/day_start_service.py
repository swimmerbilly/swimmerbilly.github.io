import json
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models import ChecklistItem, DayPlan
from app.services.assistant import AssistantError
from app.services.assistant_context import build_workspace_context
from app.services.day_start import generate_day_start_plan


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_day_plan(db: Session, plan_date: str | None = None) -> DayPlan | None:
    target = plan_date or _today_str()
    return (
        db.query(DayPlan)
        .options(joinedload(DayPlan.checklist_items))
        .filter(DayPlan.plan_date == target)
        .one_or_none()
    )


async def generate_day_plan(db: Session, plan_date: str | None = None, regenerate: bool = False) -> DayPlan:
    target = plan_date or _today_str()
    existing = get_day_plan(db, target)

    if existing and not regenerate:
        return existing

    workspace_context = build_workspace_context(db)
    ai_plan = await generate_day_start_plan(workspace_context)

    if existing:
        db.query(ChecklistItem).filter(
            ChecklistItem.day_plan_id == existing.id,
            ChecklistItem.is_user_added.is_(False),
        ).delete(synchronize_session=False)
        plan = existing
    else:
        plan = DayPlan(plan_date=target)
        db.add(plan)
        db.flush()

    plan.greeting = ai_plan.get("greeting", "")
    plan.today_focus = json.dumps(ai_plan.get("today", []))
    plan.week_focus = json.dumps(ai_plan.get("this_week", []))
    plan.month_focus = json.dumps(ai_plan.get("this_month", []))
    plan.generated_at = datetime.utcnow()

    kept_items = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.day_plan_id == plan.id, ChecklistItem.is_user_added.is_(True))
        .count()
    )

    for index, item in enumerate(ai_plan.get("checklist", [])):
        text = (item.get("text") or "").strip()
        if not text:
            continue
        priority = item.get("priority", "medium")
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        db.add(
            ChecklistItem(
                day_plan_id=plan.id,
                text=text,
                priority=priority,
                sort_order=kept_items + index,
                is_user_added=False,
            )
        )

    db.commit()
    db.refresh(plan)
    return get_day_plan(db, target) or plan


def add_checklist_item(db: Session, text: str, plan_date: str | None = None) -> ChecklistItem:
    target = plan_date or _today_str()
    label = text.strip()
    if not label:
        raise AssistantError("Checklist item cannot be empty.")

    plan = get_day_plan(db, target)
    if not plan:
        plan = DayPlan(plan_date=target, greeting="")
        db.add(plan)
        db.flush()

    max_order = (
        db.query(ChecklistItem.sort_order)
        .filter(ChecklistItem.day_plan_id == plan.id)
        .order_by(ChecklistItem.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 0

    item = ChecklistItem(
        day_plan_id=plan.id,
        text=label,
        priority="medium",
        is_user_added=True,
        sort_order=next_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def toggle_checklist_item(db: Session, item_id: int, completed: bool | None = None) -> ChecklistItem:
    item = db.get(ChecklistItem, item_id)
    if not item:
        raise AssistantError("Checklist item not found", status_code=404)
    item.is_completed = not item.is_completed if completed is None else completed
    db.commit()
    db.refresh(item)
    return item


def delete_checklist_item(db: Session, item_id: int) -> None:
    item = db.get(ChecklistItem, item_id)
    if not item:
        raise AssistantError("Checklist item not found", status_code=404)
    db.delete(item)
    db.commit()
