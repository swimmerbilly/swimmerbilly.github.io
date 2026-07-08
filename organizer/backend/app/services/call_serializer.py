from app.models import Call
from app.schemas import CallRead


def to_call_read(call: Call) -> CallRead:
    payload = CallRead.model_validate(call)
    payload.project_name = call.project.name if call.project else None
    return payload
