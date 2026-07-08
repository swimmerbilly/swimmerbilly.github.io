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


def _migrate_grasshopper_columns() -> None:
    inspector = inspect(engine)
    table_migrations = {
        "text_messages": {
            "grasshopper_message_id": "ALTER TABLE text_messages ADD COLUMN grasshopper_message_id VARCHAR(255)",
        },
        "calls": {
            "grasshopper_message_id": "ALTER TABLE calls ADD COLUMN grasshopper_message_id VARCHAR(255)",
        },
        "voicemails": {
            "grasshopper_message_id": "ALTER TABLE voicemails ADD COLUMN grasshopper_message_id VARCHAR(255)",
        },
    }

    with engine.begin() as connection:
        for table_name, migrations in table_migrations.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, statement in migrations.items():
                if column_name not in existing:
                    connection.execute(text(statement))

            connection.execute(
                text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS ix_{table_name}_grasshopper_message_id "
                    f"ON {table_name} (grasshopper_message_id) "
                    f"WHERE grasshopper_message_id IS NOT NULL"
                )
            )


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_projects_table()
    _migrate_grasshopper_columns()
