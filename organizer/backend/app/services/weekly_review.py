import json

import httpx

from app.config import settings
from app.services.assistant import AssistantError, SECRETARY_SYSTEM_PROMPT

WEEKLY_REVIEW_PROMPT = """Create a weekly review based on the workspace snapshot.

Return ONLY valid JSON:
{
  "stalled_projects": ["active projects with little or no recent communication — be specific"],
  "communication_gaps": ["projects or people you haven't heard from that you probably should follow up with"],
  "priorities": ["3-5 priorities for the rest of this week"]
}

Focus on patterns across the week. Reference real project names."""


async def generate_weekly_review(workspace_context: str) -> dict:
    if not settings.assistant_configured:
        raise AssistantError(
            "AI assistant is not configured. Set OPENAI_API_KEY in organizer/backend/.env."
        )

    system_content = SECRETARY_SYSTEM_PROMPT.format(name=settings.assistant_name)
    system_content += f"\n\n---\n\n{workspace_context}\n\n---\n\n{WEEKLY_REVIEW_PROMPT}"

    payload = {
        "model": settings.assistant_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": "Generate my weekly review."},
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
        raise AssistantError("The AI assistant returned an empty weekly review.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AssistantError("Could not parse the weekly review from the assistant.") from exc

    for key in ("stalled_projects", "communication_gaps", "priorities"):
        if key not in data:
            raise AssistantError(f"Weekly review missing required field: {key}")

    return data
