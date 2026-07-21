"""Persist and sync building permits from Boulder County jurisdictions."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import BuildingPermit, PermitSyncRun
from app.services.permit_accela import AccelaPermitClient, ScrapedPermit
from app.services.permit_jurisdictions import get_jurisdiction, list_jurisdictions
from app.services.permit_structural import detect_structural_signals, extract_engineer_from_text


def upsert_scraped_permit(
    db: Session,
    jurisdiction_id: str,
    scraped: ScrapedPermit,
    source_system: str,
) -> BuildingPermit:
    existing = (
        db.query(BuildingPermit)
        .filter(
            BuildingPermit.jurisdiction_id == jurisdiction_id,
            BuildingPermit.external_id == scraped.external_id,
        )
        .one_or_none()
    )
    payload = {
        "permit_number": scraped.permit_number,
        "permit_type": scraped.permit_type,
        "status": scraped.status,
        "description": scraped.description,
        "address": scraped.address,
        "city": scraped.city,
        "applied_at": scraped.applied_at,
        "issued_at": scraped.issued_at,
        "has_structural_plans": scraped.has_structural_plans,
        "structural_signals": json.dumps(scraped.structural_signals),
        "structural_engineer_name": scraped.structural_engineer_name,
        "structural_engineer_license": scraped.structural_engineer_license,
        "structural_engineer_firm": scraped.structural_engineer_firm,
        "source_url": scraped.source_url,
        "source_system": source_system,
        "raw_json": scraped.raw_snippet,
        "last_seen_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        permit = existing
    else:
        permit = BuildingPermit(
            jurisdiction_id=jurisdiction_id,
            external_id=scraped.external_id,
            **payload,
        )
        db.add(permit)
    db.commit()
    db.refresh(permit)
    return permit


def import_manual_permits(db: Session, rows: list[dict]) -> dict:
    created = 0
    updated = 0
    structural = 0
    for row in rows:
        jurisdiction_id = (row.get("jurisdiction_id") or "boulder_county").strip()
        permit_number = (row.get("permit_number") or "").strip()
        if not permit_number:
            continue
        external_id = (row.get("external_id") or permit_number).strip()
        description = row.get("description")
        permit_type = row.get("permit_type")
        has_structural, signals = detect_structural_signals(permit_type, description, row.get("notes"))
        if row.get("has_structural_plans") is True:
            has_structural = True
        engineer = extract_engineer_from_text(
            " ".join(
                filter(
                    None,
                    [
                        row.get("structural_engineer_name"),
                        row.get("notes"),
                        description,
                    ],
                )
            )
        )
        if row.get("structural_engineer_name"):
            engineer["name"] = row["structural_engineer_name"]
        if row.get("structural_engineer_license"):
            engineer["license"] = row["structural_engineer_license"]

        scraped = ScrapedPermit(
            external_id=external_id,
            permit_number=permit_number,
            permit_type=permit_type,
            status=row.get("status"),
            description=description,
            address=row.get("address"),
            city=row.get("city"),
            source_url=row.get("source_url"),
            has_structural_plans=has_structural,
            structural_signals=signals,
            structural_engineer_name=engineer["name"],
            structural_engineer_license=engineer["license"],
            structural_engineer_firm=row.get("structural_engineer_firm") or engineer["firm"],
            raw_snippet=json.dumps(row)[:2000],
        )
        existing = (
            db.query(BuildingPermit)
            .filter(
                BuildingPermit.jurisdiction_id == jurisdiction_id,
                BuildingPermit.external_id == external_id,
            )
            .one_or_none()
        )
        upsert_scraped_permit(db, jurisdiction_id, scraped, source_system="manual_import")
        if existing:
            updated += 1
        else:
            created += 1
        if has_structural:
            structural += 1

    return {"created": created, "updated": updated, "structural_found": structural}


async def sync_jurisdiction(db: Session, jurisdiction_id: str, max_results: int = 40) -> PermitSyncRun:
    jurisdiction = get_jurisdiction(jurisdiction_id)
    if not jurisdiction:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction_id}")

    run = PermitSyncRun(jurisdiction_id=jurisdiction_id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        if jurisdiction.system == "accela" and jurisdiction.crawlable:
            client = AccelaPermitClient(jurisdiction)
            scraped = await client.search_recent_building_permits(max_results=max_results)
            upserted = 0
            structural = 0
            for item in scraped:
                upsert_scraped_permit(db, jurisdiction_id, item, source_system="accela")
                upserted += 1
                if item.has_structural_plans:
                    structural += 1
            run.records_found = len(scraped)
            run.records_upserted = upserted
            run.structural_found = structural
            run.status = "ok"
            run.message = (
                f"Parsed {len(scraped)} Accela records for {jurisdiction.name}. "
                f"{structural} flagged with structural signals."
                if scraped
                else (
                    f"No Accela HTML results parsed for {jurisdiction.name}. "
                    "Portals change often — use Import or open the portal link and add key permits manually."
                )
            )
        elif jurisdiction.system == "energov":
            run.status = "manual"
            run.message = (
                f"{jurisdiction.name} uses EnerGov CSS. Open the portal search, then import permits "
                "with structural plans / engineer names via POST /api/permits/import. "
                f"Portal: {jurisdiction.search_url or jurisdiction.portal_url}"
            )
        else:
            run.status = "manual"
            run.message = (
                f"{jurisdiction.name} is not auto-crawlable yet. "
                f"Review {jurisdiction.portal_url} and import matching permits."
            )
    except Exception as exc:  # noqa: BLE001 - surface crawl errors to UI
        run.status = "error"
        run.message = str(exc)

    run.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run


async def sync_all_crawlable(db: Session, max_results: int = 30) -> list[PermitSyncRun]:
    runs = []
    for jurisdiction in list_jurisdictions():
        if jurisdiction.crawlable:
            runs.append(await sync_jurisdiction(db, jurisdiction.id, max_results=max_results))
    return runs


def seed_sample_permits(db: Session) -> dict:
    """Seed realistic sample rows so the UI is usable before live crawls succeed."""
    samples = [
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2026-01482",
            "permit_type": "Residential Addition",
            "status": "In Review",
            "description": "Two-story addition with foundation and structural framing. Structural plans (StructPln) uploaded.",
            "address": "1234 Mapleton Ave",
            "city": "Boulder",
            "has_structural_plans": True,
            "structural_engineer_name": "Jordan Hale",
            "structural_engineer_license": "PE-54321",
            "structural_engineer_firm": "Front Range Structural",
            "source_url": "https://energovcss.bouldercolorado.gov/EnerGov_Prod/SelfService/BoulderCO_Prod#/search",
        },
        {
            "jurisdiction_id": "boulder_county",
            "permit_number": "BP-26-0120",
            "permit_type": "New Residence",
            "status": "Issued",
            "description": "New single-family residence on unincorporated parcel. Engineered foundation required.",
            "address": "8800 N 95th St",
            "city": "Longmont",
            "has_structural_plans": True,
            "structural_engineer_name": "Alex Rivera",
            "structural_engineer_license": "PE-11882",
            "source_url": "https://aca-prod.accela.com/BOCO/Cap/CapHome.aspx?module=Building",
        },
        {
            "jurisdiction_id": "longmont",
            "permit_number": "BLD-26-3341",
            "permit_type": "Commercial Remodel",
            "status": "Under Review",
            "description": "Tenant finish with selective structural opening in bearing wall.",
            "address": "455 Main St",
            "city": "Longmont",
            "has_structural_plans": True,
            "structural_engineer_name": "Sam Okonkwo",
            "structural_engineer_firm": "Ok Structural LLC",
            "source_url": "https://aca-prod.accela.com/LONGMONT/Cap/CapHome.aspx?module=Building",
        },
        {
            "jurisdiction_id": "louisville",
            "permit_number": "RES-26-077",
            "permit_type": "Foundation Repair",
            "status": "Issued",
            "description": "Helical pier foundation repair — engineered design required.",
            "address": "912 Centennial Dr",
            "city": "Louisville",
            "has_structural_plans": True,
            "structural_engineer_name": "Casey Nguyen",
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2026-00901",
            "permit_type": "Residential Remodel",
            "status": "Issued",
            "description": "Kitchen remodel, non-structural. No structural plans required.",
            "address": "210 Pearl St",
            "city": "Boulder",
            "has_structural_plans": False,
        },
    ]
    return import_manual_permits(db, samples)
