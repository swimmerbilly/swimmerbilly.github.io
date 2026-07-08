from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AssistantConversation
from app.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantConversationRead,
    AssistantMessageRead,
    AssistantStatus,
)
from app.services.assistant import AssistantError
from app.services.assistant_chat import (
    chat_with_assistant,
    create_conversation,
    delete_conversation,
    generate_briefing,
    get_conversation_messages,
    list_conversations,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/status", response_model=AssistantStatus)
def assistant_status() -> AssistantStatus:
    return AssistantStatus(
        configured=settings.assistant_configured,
        model=settings.assistant_model,
        name=settings.assistant_name,
    )


@router.get("/conversations", response_model=list[AssistantConversationRead])
def get_conversations(db: Session = Depends(get_db)) -> list[AssistantConversationRead]:
    return list_conversations(db)


@router.post("/conversations", response_model=AssistantConversationRead, status_code=status.HTTP_201_CREATED)
def start_conversation(db: Session = Depends(get_db)) -> AssistantConversationRead:
    return create_conversation(db)


@router.get("/conversations/{conversation_id}/messages", response_model=list[AssistantMessageRead])
def get_messages(
    conversation_id: int, db: Session = Depends(get_db)
) -> list[AssistantMessageRead]:
    if not db.get(AssistantConversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return get_conversation_messages(db, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_conversation(conversation_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_conversation(db, conversation_id)
    except AssistantError as exc:
        raise HTTPException(status_code=exc.status_code or 404, detail=str(exc)) from exc


@router.post("/chat", response_model=AssistantChatResponse)
async def assistant_chat(
    payload: AssistantChatRequest, db: Session = Depends(get_db)
) -> AssistantChatResponse:
    try:
        conversation, user_message, assistant_message = await chat_with_assistant(
            db, payload.message, payload.conversation_id
        )
    except AssistantError as exc:
        status_code = exc.status_code or 400
        if status_code == 401:
            status_code = 401
        elif status_code >= 500:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return AssistantChatResponse(
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
    )


@router.post("/briefing", response_model=AssistantChatResponse)
async def assistant_briefing(
    conversation_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AssistantChatResponse:
    try:
        conversation, user_message, assistant_message = await generate_briefing(db, conversation_id)
    except AssistantError as exc:
        status_code = exc.status_code or 400
        if status_code >= 500:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return AssistantChatResponse(
        conversation=conversation,
        user_message=user_message,
        assistant_message=assistant_message,
    )
