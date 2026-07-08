from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Call, Email, Project, TextMessage, Voicemail


def build_project_contacts(db: Session, project_id: int) -> list[dict]:
    project = db.get(Project, project_id)
    if not project:
        return []

    contacts: dict[str, dict] = {}

    def upsert(
        key: str,
        name: str | None,
        phone: str | None,
        email_addr: str | None,
        role: str | None,
        source: str,
    ) -> None:
        if key not in contacts:
            contacts[key] = {
                "name": name or phone or email_addr or "Unknown",
                "phone": phone,
                "email": email_addr,
                "roles": set(),
                "sources": set(),
                "touch_count": 0,
            }
        entry = contacts[key]
        if name and (not entry["name"] or entry["name"] == "Unknown"):
            entry["name"] = name
        if phone:
            entry["phone"] = phone
        if email_addr:
            entry["email"] = email_addr
        if role:
            entry["roles"].add(role)
        entry["sources"].add(source)
        entry["touch_count"] += 1

    for call in db.query(Call).filter(Call.project_id == project_id).all():
        key = (call.phone_number or call.contact_name or f"call-{call.id}").lower()
        upsert(key, call.contact_name, call.phone_number, None, call.caller_role, "call")

    for text in db.query(TextMessage).filter(TextMessage.project_id == project_id).all():
        key = (text.phone_number or text.contact_name or f"text-{text.id}").lower()
        upsert(key, text.contact_name, text.phone_number, None, None, "text")

    for vm in db.query(Voicemail).filter(Voicemail.project_id == project_id).all():
        key = (vm.phone_number or vm.contact_name or f"vm-{vm.id}").lower()
        upsert(key, vm.contact_name, vm.phone_number, None, None, "voicemail")

    for email in db.query(Email).filter(Email.project_id == project_id).all():
        addr = email.from_address if email.direction.value == "inbound" else email.to_address
        key = addr.lower()
        upsert(key, addr.split("@")[0], None, addr, None, "email")

    result = []
    for entry in contacts.values():
        result.append(
            {
                "name": entry["name"],
                "phone": entry["phone"],
                "email": entry["email"],
                "roles": sorted(entry["roles"]) if entry["roles"] else [],
                "sources": sorted(entry["sources"]),
                "touch_count": entry["touch_count"],
            }
        )

    result.sort(key=lambda c: (-c["touch_count"], c["name"].lower()))
    return result
