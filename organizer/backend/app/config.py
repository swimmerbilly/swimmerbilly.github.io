from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Life Organizer"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'organizer.db'}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    harvest_access_token: str | None = None
    harvest_account_id: str | None = None
    harvest_user_agent: str = "Life Organizer (organizer@localhost)"

    grasshopper_imap_host: str | None = None
    grasshopper_imap_port: int = 993
    grasshopper_imap_user: str | None = None
    grasshopper_imap_password: str | None = None
    grasshopper_imap_folder: str = "INBOX"
    grasshopper_webhook_secret: str | None = None
    grasshopper_upload_dir: str = "uploads/grasshopper"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    assistant_model: str = "gpt-4o-mini"
    assistant_name: str = "Alex"

    class Config:
        env_file = ".env"

    @property
    def harvest_configured(self) -> bool:
        return bool(self.harvest_access_token and self.harvest_account_id)

    @property
    def grasshopper_imap_configured(self) -> bool:
        return bool(
            self.grasshopper_imap_host
            and self.grasshopper_imap_user
            and self.grasshopper_imap_password
        )

    @property
    def grasshopper_webhook_configured(self) -> bool:
        return bool(self.grasshopper_webhook_secret)

    @property
    def grasshopper_configured(self) -> bool:
        return self.grasshopper_imap_configured or self.grasshopper_webhook_configured

    @property
    def assistant_configured(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
