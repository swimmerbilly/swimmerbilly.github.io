import json

import httpx

from app.config import settings
from app.services.assistant import AssistantError, SECRETARY_SYSTEM_PROMPT

WRAP_UP_PROMPT = """Create an end-of-day wrap-up based on the workspace snapshot and today's checklist progress.

Return ONLY valid JSON:
{
  "summary": "2-3 sentences on how the day went — celebrate wins, note what slipped",
  "completed": ["things that appear done or handled today"],
  "slipped": ["items that still need attention tomorrow"],
  "tomorrow": ["top 3 priorities for tomorrow morning"]
}

Be specific. Reference real project names and communications when possible."""


async def generate_wrap_up(workspace_context: str, checklist_summary: str) -> dict:
    if not settings.assistant_configured:
        raise AssistantError(
            "AI assistant is not configured. Set OPENAI_API_KEY in organizer/backend/.env."
        )

    system_content = SECRETARY_SYSTEM_PROMPT.format(name=settings.assistant_name)
    system_content += f"\n\n---\n\n{workspace_context}\n\nToday's checklist:\n{checklist_summary}\n\n---\n\n{WRAP_UP_PROMPT}"

    payload = {
        "model": settings.assistant_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": "Generate my end-of-day wrap-up."},
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
        raise AssistantError("The AI assistant returned an empty wrap-up.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AssistantError("Could not parse the wrap-up from the assistant.") from exc

    for key in ("summary", "completed", "slipped", "tomorrow"):
        if key not in data:
            raise AssistantError(f"Wrap-up missing required field: {key}")

    return data
