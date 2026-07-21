from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BuildingPermit
from app.schemas import (
    BuildingPermitRead,
    JurisdictionRead,
    MarketResearchReport,
    PermitImportRequest,
    PermitImportResult,
    PermitStats,
    PermitSyncRunRead,
)
from app.services.market_research import build_market_research
from app.services.permit_jurisdictions import list_jurisdictions
from app.services.permit_sync import (
    import_manual_permits,
    seed_sample_permits,
    sync_all_crawlable,
    sync_jurisdiction,
)

router = APIRouter(prefix="/permits", tags=["permits"])


@router.get("/jurisdictions", response_model=list[JurisdictionRead])
def get_jurisdictions() -> list[JurisdictionRead]:
    return [
        JurisdictionRead(
            id=j.id,
            name=j.name,
            kind=j.kind,
            system=j.system,
            portal_url=j.portal_url,
            search_url=j.search_url,
            notes=j.notes,
            crawlable=j.crawlable,
        )
        for j in list_jurisdictions()
    ]


@router.get("/stats", response_model=PermitStats)
def permit_stats(db: Session = Depends(get_db)) -> PermitStats:
    permits = db.query(BuildingPermit).all()
    by_jurisdiction: dict[str, int] = {}
    structural = 0
    with_engineer = 0
    with_contractor = 0
    with_architect = 0
    total_value = 0.0
    for permit in permits:
        by_jurisdiction[permit.jurisdiction_id] = by_jurisdiction.get(permit.jurisdiction_id, 0) + 1
        if permit.has_structural_plans:
            structural += 1
        if permit.structural_engineer_name or permit.structural_engineer_firm:
            with_engineer += 1
        if permit.contractor_name:
            with_contractor += 1
        if permit.architect_name or permit.architect_firm:
            with_architect += 1
        if permit.estimated_value_amount:
            total_value += float(permit.estimated_value_amount)
    return PermitStats(
        total=len(permits),
        with_structural_plans=structural,
        with_engineer_named=with_engineer,
        with_contractor=with_contractor,
        with_architect=with_architect,
        total_estimated_value=round(total_value, 2),
        by_jurisdiction=by_jurisdiction,
    )


@router.get("/market-research", response_model=MarketResearchReport)
def market_research(
    jurisdiction_id: str | None = Query(default=None),
    months: int = Query(default=24, ge=1, le=120),
    structural_only: bool = Query(default=False),
    q: str | None = Query(default=None),
    limit: int = Query(default=40, ge=5, le=100),
    db: Session = Depends(get_db),
) -> MarketResearchReport:
    report = build_market_research(
        db,
        jurisdiction_id=jurisdiction_id,
        months=months,
        structural_only=structural_only,
        q=q,
        limit=limit,
    )
    return MarketResearchReport(**report)


@router.get("", response_model=list[BuildingPermitRead])
def list_permits(
    jurisdiction_id: str | None = Query(default=None),
    structural_only: bool = Query(default=False),
    engineer: str | None = Query(default=None),
    contractor: str | None = Query(default=None),
    architect: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[BuildingPermitRead]:
    query = db.query(BuildingPermit)
    if jurisdiction_id:
        query = query.filter(BuildingPermit.jurisdiction_id == jurisdiction_id)
    if structural_only:
        query = query.filter(BuildingPermit.has_structural_plans.is_(True))
    if engineer:
        like = f"%{engineer.strip()}%"
        query = query.filter(
            (BuildingPermit.structural_engineer_name.ilike(like))
            | (BuildingPermit.structural_engineer_firm.ilike(like))
        )
    if contractor:
        like = f"%{contractor.strip()}%"
        query = query.filter(BuildingPermit.contractor_name.ilike(like))
    if architect:
        like = f"%{architect.strip()}%"
        query = query.filter(
            (BuildingPermit.architect_name.ilike(like))
            | (BuildingPermit.architect_firm.ilike(like))
        )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (BuildingPermit.permit_number.ilike(like))
            | (BuildingPermit.address.ilike(like))
            | (BuildingPermit.description.ilike(like))
            | (BuildingPermit.permit_type.ilike(like))
            | (BuildingPermit.contractor_name.ilike(like))
            | (BuildingPermit.architect_firm.ilike(like))
            | (BuildingPermit.structural_engineer_name.ilike(like))
        )
    permits = query.order_by(BuildingPermit.updated_at.desc()).limit(limit).all()
    return [BuildingPermitRead.from_model(p) for p in permits]


@router.post("/sync/{jurisdiction_id}", response_model=PermitSyncRunRead)
async def sync_one_jurisdiction(
    jurisdiction_id: str,
    max_results: int = Query(default=40, ge=5, le=5000),
    since: str = Query(default="2023-01-01"),
    db: Session = Depends(get_db),
) -> PermitSyncRunRead:
    try:
        run = await sync_jurisdiction(
            db, jurisdiction_id, max_results=max_results, since=since
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return run


@router.post("/sync", response_model=list[PermitSyncRunRead])
async def sync_crawlable_jurisdictions(
    max_results: int = Query(default=1500, ge=5, le=5000),
    since: str = Query(default="2023-01-01"),
    db: Session = Depends(get_db),
) -> list[PermitSyncRunRead]:
    return await sync_all_crawlable(db, max_results=max_results, since=since)


@router.post("/import", response_model=PermitImportResult)
def import_permits(payload: PermitImportRequest, db: Session = Depends(get_db)) -> PermitImportResult:
    if not payload.permits:
        raise HTTPException(status_code=400, detail="No permits provided")
    result = import_manual_permits(db, payload.permits)
    return PermitImportResult(**result)


@router.post("/seed-sample", response_model=PermitImportResult)
def seed_samples(db: Session = Depends(get_db)) -> PermitImportResult:
    result = seed_sample_permits(db)
    return PermitImportResult(**result)
