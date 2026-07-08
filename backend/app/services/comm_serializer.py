from app.models import Email, TextMessage, Voicemail
from app.schemas import EmailRead, TextRead, VoicemailRead


def _project_meta(entity) -> tuple[str | None, str | None]:
    if entity.project:
        return entity.project.name, entity.project.color
    return None, None


def to_email_read(email: Email) -> EmailRead:
    payload = EmailRead.model_validate(email)
    payload.project_name, payload.project_color = _project_meta(email)
    return payload


def to_text_read(text: TextMessage) -> TextRead:
    payload = TextRead.model_validate(text)
    payload.project_name, payload.project_color = _project_meta(text)
    return payload


def to_voicemail_read(voicemail: Voicemail) -> VoicemailRead:
    payload = VoicemailRead.model_validate(voicemail)
    payload.project_name, payload.project_color = _project_meta(voicemail)
    return payload
