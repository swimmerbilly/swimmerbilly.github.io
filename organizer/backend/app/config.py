from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Life Organizer"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'organizer.db'}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    harvest_access_token: str | None = None
    harvest_account_id: str | None = None
    harvest_user_agent: str = "Life Organizer (organizer@localhost)"

    class Config:
        env_file = ".env"

    @property
    def harvest_configured(self) -> bool:
        return bool(self.harvest_access_token and self.harvest_account_id)


settings = Settings()
