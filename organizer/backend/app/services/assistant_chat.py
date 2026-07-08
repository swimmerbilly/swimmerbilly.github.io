from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AssistantConversation, AssistantMessage
from app.services.assistant import AssistantError, generate_assistant_reply
from app.services.assistant_context import build_workspace_context

MAX_HISTORY_MESSAGES = 20


def _conversation_title(first_message: str) -> str:
    cleaned = " ".join(first_message.split())
    if len(cleaned) <= 48:
        return cleaned or "New conversation"
    return cleaned[:45] + "..."


def list_conversations(db: Session) -> list[AssistantConversation]:
    return (
        db.query(AssistantConversation)
        .order_by(AssistantConversation.updated_at.desc())
        .all()
    )


def get_conversation_messages(db: Session, conversation_id: int) -> list[AssistantMessage]:
    return (
        db.query(AssistantMessage)
        .filter(AssistantMessage.conversation_id == conversation_id)
        .order_by(AssistantMessage.created_at.asc())
        .all()
    )


def create_conversation(db: Session, title: str = "New conversation") -> AssistantConversation:
    conversation = AssistantConversation(title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_id: int) -> None:
    conversation = db.get(AssistantConversation, conversation_id)
    if not conversation:
        raise AssistantError("Conversation not found", status_code=404)
    db.delete(conversation)
    db.commit()


async def chat_with_assistant(
    db: Session,
    user_message: str,
    conversation_id: int | None = None,
) -> tuple[AssistantConversation, AssistantMessage, AssistantMessage]:
    message = user_message.strip()
    if not message:
        raise AssistantError("Message cannot be empty.")

    if conversation_id:
        conversation = db.get(AssistantConversation, conversation_id)
        if not conversation:
            raise AssistantError("Conversation not found", status_code=404)
    else:
        conversation = create_conversation(db, _conversation_title(message))

    user_entry = AssistantMessage(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_entry)
    db.flush()

    history = get_conversation_messages(db, conversation.id)
    history_payload = [{"role": m.role, "content": m.content} for m in history[-MAX_HISTORY_MESSAGES:]]

    workspace_context = build_workspace_context(db)
    reply_text = await generate_assistant_reply(history_payload, workspace_context)

    assistant_entry = AssistantMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_entry)

    if conversation.title == "New conversation" or (
        len(history) <= 1 and conversation.title != _conversation_title(message)
    ):
        conversation.title = _conversation_title(message)

    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    db.refresh(user_entry)
    db.refresh(assistant_entry)

    return conversation, user_entry, assistant_entry


async def generate_briefing(db: Session, conversation_id: int | None = None) -> tuple[
    AssistantConversation, AssistantMessage, AssistantMessage
]:
    prompt = (
        "Give me a concise morning briefing. Prioritize what needs my attention today, "
        "flag anything urgent in emails, texts, calls, or voicemails, and suggest 3 concrete next actions."
    )
    return await chat_with_assistant(db, prompt, conversation_id)
