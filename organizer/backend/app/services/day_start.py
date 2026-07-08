import json

import httpx

from app.config import settings
from app.services.assistant import AssistantError, SECRETARY_SYSTEM_PROMPT

DAY_START_PROMPT = """Create a helpful start-of-day plan based on the workspace snapshot.

Return ONLY valid JSON with this exact structure:
{
  "greeting": "Warm 1-2 sentence greeting to start the day",
  "today": ["3-5 specific priorities for TODAY only"],
  "this_week": ["3-4 items to keep on radar THIS WEEK"],
  "this_month": ["2-3 bigger-picture goals for THIS MONTH"],
  "checklist": [
    {"text": "Concrete actionable task the user can check off", "priority": "high"},
    {"text": "Another task", "priority": "medium"}
  ]
}

Rules:
- Include 6-10 checklist items mixing: unread communications, call follow-ups, and project work
- Reference real project names and communications from the snapshot when possible
- priority must be "high", "medium", or "low" (high = must do today)
- Be specific and actionable — no generic advice like "check email"
- If the workspace is empty, guide them to sync Harvest, email, or Grasshopper"""


async def generate_day_start_plan(workspace_context: str) -> dict:
    if not settings.assistant_configured:
        raise AssistantError(
            "AI assistant is not configured. Set OPENAI_API_KEY in organizer/backend/.env."
        )

    system_content = SECRETARY_SYSTEM_PROMPT.format(name=settings.assistant_name)
    system_content += f"\n\n---\n\n{workspace_context}\n\n---\n\n{DAY_START_PROMPT}"

    payload = {
        "model": settings.assistant_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": "Generate my start-of-day plan for today."},
        ],
        "temperature": 0.35,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("error", {}).get("message", detail)
        except ValueError:
            pass
        raise AssistantError(detail, status_code=response.status_code)

    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise AssistantError("The AI assistant returned an empty day plan.")

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AssistantError("Could not parse the day plan from the assistant.") from exc

    for key in ("greeting", "today", "this_week", "this_month", "checklist"):
        if key not in plan:
            raise AssistantError(f"Day plan missing required field: {key}")

    return plan
