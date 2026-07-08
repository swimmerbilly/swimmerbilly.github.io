import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models import ChecklistItem, DayPlan, Call
from app.services.assistant import AssistantError
from app.services.assistant_context import build_workspace_context
from app.services.day_start import generate_day_start_plan
from app.services.day_wrap_up import generate_wrap_up
from app.services.weekly_review import generate_weekly_review


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


def _checklist_summary(plan: DayPlan) -> str:
    lines = []
    for item in sorted(plan.checklist_items, key=lambda i: i.sort_order):
        status = "done" if item.is_completed else "open"
        lines.append(f"- [{status}] {item.text}")
    return "\n".join(lines) if lines else "No checklist items yet."


async def generate_wrap_up_plan(db: Session, plan_date: str | None = None) -> DayPlan:
    target = plan_date or _today_str()
    plan = get_day_plan(db, target)
    if not plan:
        plan = DayPlan(plan_date=target, greeting="")
        db.add(plan)
        db.flush()

    workspace_context = build_workspace_context(db)
    wrap_up = await generate_wrap_up(workspace_context, _checklist_summary(plan))

    plan.wrap_up_summary = wrap_up.get("summary", "")
    plan.wrap_up_tomorrow = json.dumps(
        {
            "tomorrow": wrap_up.get("tomorrow", []),
            "completed": wrap_up.get("completed", []),
            "slipped": wrap_up.get("slipped", []),
        }
    )
    plan.wrap_up_generated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return get_day_plan(db, target) or plan


async def generate_weekly_review_plan(db: Session, plan_date: str | None = None) -> DayPlan:
    target = plan_date or _today_str()
    plan = get_day_plan(db, target)
    if not plan:
        plan = DayPlan(plan_date=target, greeting="")
        db.add(plan)
        db.flush()

    workspace_context = build_workspace_context(db)
    review = await generate_weekly_review(workspace_context)

    plan.weekly_review_stalled = json.dumps(review.get("stalled_projects", []))
    plan.weekly_review_gaps = json.dumps(review.get("communication_gaps", []))
    plan.weekly_review_priorities = json.dumps(review.get("priorities", []))
    plan.weekly_review_generated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return get_day_plan(db, target) or plan


def get_due_follow_ups(db: Session) -> list:
    now = datetime.utcnow()
    return (
        db.query(Call)
        .filter(
            Call.follow_up_at.isnot(None),
            Call.follow_up_completed.is_(False),
            Call.follow_up_at <= now + timedelta(days=1),
        )
        .order_by(Call.follow_up_at.asc())
        .limit(10)
        .all()
    )
