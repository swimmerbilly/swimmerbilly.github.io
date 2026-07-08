from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import assistant, attention, calls, dashboard, day_start, emails, grasshopper, harvest, linking, mailboxes, projects, texts, voicemails


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(harvest.router, prefix="/api")
app.include_router(grasshopper.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(mailboxes.router, prefix="/api")
app.include_router(texts.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(voicemails.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(day_start.router, prefix="/api")
app.include_router(attention.router, prefix="/api")
app.include_router(linking.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")

uploads_dir = Path(__file__).resolve().parent.parent / settings.grasshopper_upload_dir
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir.parent), name="uploads")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
