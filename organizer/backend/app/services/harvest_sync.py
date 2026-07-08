from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Project, ProjectStatus
from app.services.harvest import HarvestClient, HarvestError

HARVEST_COLORS = ["#3b82f6", "#34d399", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]


def color_for_harvest_id(harvest_id: int) -> str:
    return HARVEST_COLORS[harvest_id % len(HARVEST_COLORS)]


def build_description(harvest_project: dict) -> str | None:
    parts: list[str] = []
    client = harvest_project.get("client") or {}
    client_name = client.get("name")
    code = harvest_project.get("code")
    notes = (harvest_project.get("notes") or "").strip()

    if client_name:
        parts.append(f"Client: {client_name}")
    if code:
        parts.append(f"Code: {code}")
    if notes:
        parts.append(notes)

    return "\n".join(parts) or None


def map_harvest_status(is_active: bool) -> ProjectStatus:
    return ProjectStatus.ACTIVE if is_active else ProjectStatus.ARCHIVED


def apply_harvest_project(project: Project, harvest_project: dict) -> None:
    client = harvest_project.get("client") or {}
    project.harvest_id = harvest_project["id"]
    project.name = harvest_project["name"]
    project.description = build_description(harvest_project)
    project.status = map_harvest_status(harvest_project.get("is_active", True))
    project.color = color_for_harvest_id(harvest_project["id"])
    project.harvest_client_name = client.get("name")
    project.harvest_code = harvest_project.get("code")
    project.harvest_synced_at = datetime.utcnow()


async def sync_projects_from_harvest(db: Session, client: HarvestClient | None = None) -> dict:
    harvest = client or HarvestClient()
    if not harvest.is_configured:
        raise HarvestError("Harvest is not configured. Set HARVEST_ACCESS_TOKEN and HARVEST_ACCOUNT_ID.")

    harvest_projects = await harvest.list_projects()
    seen_harvest_ids: set[int] = set()
    created = 0
    updated = 0

    for harvest_project in harvest_projects:
        harvest_id = harvest_project["id"]
        seen_harvest_ids.add(harvest_id)

        project = db.query(Project).filter(Project.harvest_id == harvest_id).one_or_none()
        if project:
            apply_harvest_project(project, harvest_project)
            updated += 1
        else:
            project = Project(
                name=harvest_project["name"],
                color=color_for_harvest_id(harvest_id),
            )
            apply_harvest_project(project, harvest_project)
            db.add(project)
            created += 1

    archived = 0
    local_harvest_projects = db.query(Project).filter(Project.harvest_id.isnot(None)).all()
    for project in local_harvest_projects:
        if project.harvest_id not in seen_harvest_ids:
            project.status = ProjectStatus.ARCHIVED
            project.harvest_synced_at = datetime.utcnow()
            archived += 1

    db.commit()

    return {
        "synced": len(harvest_projects),
        "created": created,
        "updated": updated,
        "archived": archived,
    }
