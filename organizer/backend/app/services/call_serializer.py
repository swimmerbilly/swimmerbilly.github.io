from app.models import Call
from app.schemas import CallRead


def to_call_read(call: Call) -> CallRead:
    payload = CallRead.model_validate(call)
    if call.project:
        payload.project_name = call.project.name
        payload.project_color = call.project.color
    return payload
