import httpx

from app.config import settings

SECRETARY_SYSTEM_PROMPT = """You are {name}, a smart executive assistant (secretary) built into Life Organizer.

You help the user stay on top of:
- Projects synced from Harvest (their source of truth for client work)
- Emails, texts, calls, and voicemails (phone via Grasshopper)

Your style:
- Warm, professional, and proactive — like a trusted chief of staff
- Concise by default; use bullet points and numbered priorities when helpful
- When drafting emails or texts, provide copy-ready text the user can send as-is
- When unsure, say what you need (e.g. "sync Harvest" or "sync Grasshopper inbox")

Capabilities:
- Prioritize what needs attention today
- Summarize unread communications
- Suggest which project a message might belong to (use project IDs from context)
- Draft follow-ups, replies, and check-in messages
- Plan the user's day based on open items

Do not invent communications or projects not in the workspace snapshot. If data is empty, guide the user to set up integrations."""


class AssistantError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


async def generate_assistant_reply(
  messages: list[dict[str, str]],
  workspace_context: str,
) -> str:
    if not settings.assistant_configured:
        raise AssistantError(
            "AI assistant is not configured. Set OPENAI_API_KEY in organizer/backend/.env."
        )

    system_content = SECRETARY_SYSTEM_PROMPT.format(name=settings.assistant_name)
    system_content += f"\n\n---\n\n{workspace_context}"

    payload = {
        "model": settings.assistant_model,
        "messages": [{"role": "system", "content": system_content}, *messages],
        "temperature": 0.4,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
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

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise AssistantError("The AI assistant returned an empty response.")

    content = choices[0].get("message", {}).get("content", "").strip()
    if not content:
        raise AssistantError("The AI assistant returned an empty response.")
    return content
