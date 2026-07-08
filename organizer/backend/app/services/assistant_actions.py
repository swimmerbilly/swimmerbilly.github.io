import asyncio
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Call, Email, TextMessage, Voicemail
from app.services.assistant import AssistantError
from app.services.day_start_service import generate_day_plan
from app.services.email_sync import sync_all_mailboxes
from app.services.grasshopper_sync import sync_grasshopper_from_imap
from app.services.harvest_sync import sync_projects_from_harvest
from app.services.project_linking import link_comm_to_project

ACTIONS_PATTERN = re.compile(r"\[ACTIONS\]\s*(\[.*?\])\s*\[/ACTIONS\]", re.DOTALL)


def strip_actions_from_reply(content: str) -> tuple[str, list[dict]]:
    match = ACTIONS_PATTERN.search(content)
    if not match:
        return content.strip(), []

    actions_raw = match.group(1)
    visible = (content[: match.start()] + content[match.end() :]).strip()
    try:
        actions = json.loads(actions_raw)
        if not isinstance(actions, list):
            actions = []
    except json.JSONDecodeError:
        actions = []
    return visible, actions


def normalize_action(action: dict) -> dict:
    action_type = action.get("type", "")
    label = action.get("label") or _default_label(action_type, action)
    return {
        "type": action_type,
        "label": label,
        "params": {k: v for k, v in action.items() if k not in {"type", "label"}},
    }


def _default_label(action_type: str, action: dict) -> str:
    labels = {
        "link_email": "Link email to project",
        "link_text": "Link text to project",
        "link_voicemail": "Link voicemail to project",
        "link_call": "Link call to project",
        "mark_email_read": "Mark email as read",
        "mark_text_read": "Mark text as read",
        "mark_voicemail_listened": "Mark voicemail as listened",
        "sync_harvest": "Sync Harvest projects",
        "sync_mailboxes": "Sync email inboxes",
        "sync_grasshopper": "Sync Grasshopper",
        "refresh_day_plan": "Refresh today's brief",
    }
    return labels.get(action_type, action_type.replace("_", " ").title())


async def execute_action(db: Session, action: dict) -> dict[str, Any]:
    action_type = action.get("type", "")
    params = action.get("params") or action

    if action_type == "link_email":
        ok = link_comm_to_project(db, "email", int(params["email_id"]), int(params["project_id"]))
        return {"success": ok, "message": "Email linked to project." if ok else "Could not link email."}

    if action_type == "link_text":
        ok = link_comm_to_project(db, "text", int(params["text_id"]), int(params["project_id"]))
        return {"success": ok, "message": "Text linked to project." if ok else "Could not link text."}

    if action_type == "link_voicemail":
        ok = link_comm_to_project(db, "voicemail", int(params["voicemail_id"]), int(params["project_id"]))
        return {"success": ok, "message": "Voicemail linked to project." if ok else "Could not link voicemail."}

    if action_type == "link_call":
        ok = link_comm_to_project(db, "call", int(params["call_id"]), int(params["project_id"]))
        return {"success": ok, "message": "Call linked to project." if ok else "Could not link call."}

    if action_type == "mark_email_read":
        email = db.get(Email, int(params["email_id"]))
        if not email:
            return {"success": False, "message": "Email not found."}
        email.is_read = True
        db.commit()
        return {"success": True, "message": "Email marked as read."}

    if action_type == "mark_text_read":
        text = db.get(TextMessage, int(params["text_id"]))
        if not text:
            return {"success": False, "message": "Text not found."}
        text.is_read = True
        db.commit()
        return {"success": True, "message": "Text marked as read."}

    if action_type == "mark_voicemail_listened":
        vm = db.get(Voicemail, int(params["voicemail_id"]))
        if not vm:
            return {"success": False, "message": "Voicemail not found."}
        vm.is_listened = True
        db.commit()
        return {"success": True, "message": "Voicemail marked as listened."}

    if action_type == "sync_harvest":
        result = await sync_projects_from_harvest(db)
        return {"success": True, "message": f"Synced {result['synced']} Harvest projects.", "result": result}

    if action_type == "sync_mailboxes":
        result = await asyncio.to_thread(sync_all_mailboxes, db)
        return {"success": True, "message": f"Synced mailboxes ({result['created']} new emails).", "result": result}

    if action_type == "sync_grasshopper":
        result = await asyncio.to_thread(sync_grasshopper_from_imap, db)
        return {"success": True, "message": f"Grasshopper sync complete ({result['events_found']} events).", "result": result}

    if action_type == "refresh_day_plan":
        await generate_day_plan(db, regenerate=True)
        return {"success": True, "message": "Today's brief refreshed."}

    raise AssistantError(f"Unknown action type: {action_type}")
