"""Persist integration credentials in SQLite and apply to runtime settings."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings

SECRET_KEYS = {
    "harvest_access_token",
    "work_email_imap_password",
    "personal_email_imap_password",
    "openai_api_key",
    "grasshopper_webhook_secret",
    "grasshopper_imap_password",
}

SETTING_KEYS = [
    "harvest_access_token",
    "harvest_account_id",
    "harvest_user_agent",
    "work_email_imap_host",
    "work_email_imap_port",
    "work_email_imap_user",
    "work_email_imap_password",
    "work_email_imap_folder",
    "personal_email_imap_host",
    "personal_email_imap_port",
    "personal_email_imap_user",
    "personal_email_imap_password",
    "personal_email_imap_folder",
    "openai_api_key",
    "openai_base_url",
    "assistant_model",
    "assistant_name",
    "grasshopper_webhook_secret",
]


def _mask(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return "••••"
    return f"••••{value[-4:]}"


def load_settings_from_db(db: Session) -> None:
    from app.models import AppSetting

    rows = db.query(AppSetting).all()
    for row in rows:
        if row.key in SETTING_KEYS and row.value:
            _apply_key(row.key, row.value)


def _apply_key(key: str, value: str) -> None:
    if not hasattr(settings, key):
        return
    if key.endswith("_port"):
        try:
            setattr(settings, key, int(value))
        except ValueError:
            setattr(settings, key, value)
    else:
        setattr(settings, key, value)


def get_stored_values(db: Session) -> dict[str, str]:
    from app.models import AppSetting

    return {row.key: row.value for row in db.query(AppSetting).all()}


def save_settings(db: Session, payload: dict[str, str | int | None]) -> None:
    from app.models import AppSetting

    stored = get_stored_values(db)
    for key, raw in payload.items():
        if key not in SETTING_KEYS:
            continue
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        if key in SECRET_KEYS and value.startswith("••••"):
            continue

        row = db.get(AppSetting, key)
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            db.add(AppSetting(key=key, value=value))
        _apply_key(key, value)

    db.commit()


def build_setup_status(db: Session) -> dict:
    stored = get_stored_values(db)

    def field(key: str, label: str, secret: bool = False, placeholder: str = "") -> dict:
        current = stored.get(key) or getattr(settings, key, None)
        if current is not None and not isinstance(current, str):
            current = str(current)
        return {
            "key": key,
            "label": label,
            "value": None if secret and current else (current or ""),
            "masked": _mask(current) if secret and current else None,
            "has_value": bool(current),
            "placeholder": placeholder,
            "secret": secret,
        }

    harvest_fields = [
        field("harvest_access_token", "Personal Access Token", secret=True, placeholder="From Harvest Developers"),
        field("harvest_account_id", "Account ID", placeholder="Numeric account ID"),
        field("harvest_user_agent", "User agent", placeholder="Personal Assistant (you@example.com)"),
    ]
    work_email_fields = [
        field("work_email_imap_host", "IMAP host", placeholder="outlook.office365.com"),
        field("work_email_imap_user", "Email address", placeholder="you@yourcompany.com"),
        field("work_email_imap_password", "App password", secret=True),
    ]
    personal_email_fields = [
        field("personal_email_imap_host", "IMAP host", placeholder="imap.gmail.com"),
        field("personal_email_imap_user", "Gmail address", placeholder="you@gmail.com"),
        field("personal_email_imap_password", "App password", secret=True),
    ]
    assistant_fields = [
        field("openai_api_key", "OpenAI API key", secret=True),
        field("assistant_name", "Assistant name", placeholder="Alex"),
        field("assistant_model", "Model", placeholder="gpt-4o-mini"),
    ]
    grasshopper_fields = [
        field(
            "grasshopper_webhook_secret",
            "Webhook secret (optional)",
            secret=True,
            placeholder="For Zapier / custom automations",
        ),
    ]

    steps = [
        {
            "id": "harvest",
            "title": "Harvest",
            "description": "Sync your projects from Harvest.",
            "help_url": "https://id.getharvest.com/developers",
            "configured": settings.harvest_configured,
            "fields": harvest_fields,
        },
        {
            "id": "work_email",
            "title": "Work email (Outlook)",
            "description": "Company Outlook / Microsoft 365 inbox.",
            "help_text": "Use an app password if MFA is enabled. Host is usually outlook.office365.com.",
            "configured": settings.work_email_configured,
            "fields": work_email_fields,
        },
        {
            "id": "personal_email",
            "title": "Personal email (Gmail)",
            "description": "Personal Gmail inbox (optional but recommended).",
            "help_text": "Enable IMAP in Gmail and create a Google app password.",
            "configured": settings.personal_email_configured,
            "fields": personal_email_fields,
        },
        {
            "id": "assistant",
            "title": "AI assistant (Alex)",
            "description": "Powers Start My Day, briefings, and draft replies.",
            "configured": settings.assistant_configured,
            "fields": assistant_fields,
        },
        {
            "id": "grasshopper",
            "title": "Grasshopper phone",
            "description": "Voicemails sync via your work Outlook inbox. Point Grasshopper notifications to that address.",
            "configured": settings.grasshopper_imap_configured,
            "fields": grasshopper_fields,
            "optional": True,
        },
    ]

    required_done = (
        settings.harvest_configured
        and settings.work_email_configured
        and settings.assistant_configured
    )

    return {
        "steps": steps,
        "required_configured": required_done,
        "any_email_configured": settings.email_sync_configured,
    }


STEP_FIELD_MAP: dict[str, list[str]] = {
    "harvest": ["harvest_access_token", "harvest_account_id", "harvest_user_agent"],
    "work_email": [
        "work_email_imap_host",
        "work_email_imap_user",
        "work_email_imap_password",
        "work_email_imap_folder",
    ],
    "personal_email": [
        "personal_email_imap_host",
        "personal_email_imap_user",
        "personal_email_imap_password",
        "personal_email_imap_folder",
    ],
    "assistant": ["openai_api_key", "assistant_name", "assistant_model", "openai_base_url"],
    "grasshopper": ["grasshopper_webhook_secret"],
}

STEP_DEFAULTS: dict[str, dict[str, str]] = {
    "work_email": {
        "work_email_imap_host": "outlook.office365.com",
        "work_email_imap_folder": "INBOX",
    },
    "personal_email": {
        "personal_email_imap_host": "imap.gmail.com",
        "personal_email_imap_folder": "INBOX",
    },
    "assistant": {
        "assistant_name": "Alex",
        "assistant_model": "gpt-4o-mini",
        "openai_base_url": "https://api.openai.com/v1",
    },
    "harvest": {
        "harvest_user_agent": "Personal Assistant (you@example.com)",
    },
}
