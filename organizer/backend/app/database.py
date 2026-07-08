from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_projects_table() -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("projects")}
    migrations = {
        "harvest_id": "ALTER TABLE projects ADD COLUMN harvest_id INTEGER",
        "harvest_client_name": "ALTER TABLE projects ADD COLUMN harvest_client_name VARCHAR(200)",
        "harvest_code": "ALTER TABLE projects ADD COLUMN harvest_code VARCHAR(50)",
        "harvest_synced_at": "ALTER TABLE projects ADD COLUMN harvest_synced_at DATETIME",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing:
                connection.execute(text(statement))

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_harvest_id "
                "ON projects (harvest_id) WHERE harvest_id IS NOT NULL"
            )
        )


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_projects_table()
