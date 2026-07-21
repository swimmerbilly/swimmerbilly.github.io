"""Persist and sync building permits from Boulder County jurisdictions."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import BuildingPermit, PermitSyncRun
from app.services.permit_accela import AccelaPermitClient, ScrapedPermit
from app.services.permit_boulder_opendata import BoulderOpenDataClient
from app.services.permit_jurisdictions import get_jurisdiction, list_jurisdictions
from app.services.permit_structural import (
    detect_structural_signals,
    extract_architect_from_text,
    extract_engineer_from_text,
    parse_money,
)


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
        "work_type": scraped.work_type,
        "status": scraped.status,
        "description": scraped.description,
        "address": scraped.address,
        "city": scraped.city,
        "applied_at": scraped.applied_at,
        "issued_at": scraped.issued_at,
        "estimated_value": scraped.estimated_value,
        "estimated_value_amount": scraped.estimated_value_amount,
        "contractor_name": scraped.contractor_name,
        "contractor_trade": scraped.contractor_trade,
        "architect_name": scraped.architect_name,
        "architect_firm": scraped.architect_firm,
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
            # Don't wipe richer professional fields with empty open-data blanks
            if key in {
                "architect_name",
                "architect_firm",
                "structural_engineer_name",
                "structural_engineer_license",
                "structural_engineer_firm",
                "contractor_name",
            } and not value:
                continue
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
        notes = row.get("notes")
        has_structural, signals = detect_structural_signals(permit_type, description, notes)
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
        if row.get("structural_engineer_firm"):
            engineer["firm"] = row["structural_engineer_firm"]

        architect = extract_architect_from_text(
            " ".join(filter(None, [row.get("architect_name"), row.get("architect_firm"), notes, description]))
        )
        if row.get("architect_name"):
            architect["name"] = row["architect_name"]
        if row.get("architect_firm"):
            architect["firm"] = row["architect_firm"]

        amount = parse_money(row.get("estimated_value_amount") or row.get("estimated_value"))
        scraped = ScrapedPermit(
            external_id=external_id,
            permit_number=permit_number,
            permit_type=permit_type,
            work_type=row.get("work_type"),
            status=row.get("status"),
            description=description,
            address=row.get("address"),
            city=row.get("city"),
            applied_at=None,
            issued_at=None,
            estimated_value=str(row.get("estimated_value")) if row.get("estimated_value") is not None else None,
            estimated_value_amount=amount,
            contractor_name=row.get("contractor_name"),
            contractor_trade=row.get("contractor_trade"),
            architect_name=architect["name"],
            architect_firm=architect["firm"],
            source_url=row.get("source_url"),
            has_structural_plans=has_structural,
            structural_signals=signals,
            structural_engineer_name=engineer["name"],
            structural_engineer_license=engineer["license"],
            structural_engineer_firm=engineer["firm"] or row.get("structural_engineer_firm"),
            raw_snippet=json.dumps(row)[:2000],
        )
        # optional ISO dates
        for field, attr in (("applied_at", "applied_at"), ("issued_at", "issued_at")):
            raw = row.get(field)
            if isinstance(raw, str) and raw:
                try:
                    setattr(scraped, attr, datetime.fromisoformat(raw.replace("Z", "")))
                except ValueError:
                    pass

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


async def sync_jurisdiction(
    db: Session,
    jurisdiction_id: str,
    max_results: int = 40,
    since: str = "2023-01-01",
) -> PermitSyncRun:
    jurisdiction = get_jurisdiction(jurisdiction_id)
    if not jurisdiction:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction_id}")

    run = PermitSyncRun(jurisdiction_id=jurisdiction_id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        if jurisdiction.id == "city_of_boulder" or jurisdiction.system == "opendata":
            client = BoulderOpenDataClient()
            scraped = await client.fetch_building_permits(
                since=since,
                max_records=max(max_results, 100),
            )
            upserted = 0
            structural = 0
            for item in scraped:
                upsert_scraped_permit(db, "city_of_boulder", item, source_system="boulder_opendata")
                upserted += 1
                if item.has_structural_plans:
                    structural += 1
            run.records_found = len(scraped)
            run.records_upserted = upserted
            run.structural_found = structural
            run.status = "ok"
            run.message = (
                f"Imported {upserted} City of Boulder open-data permits since {since} "
                f"({structural} with structural signals). Contractor + $ value are strong; "
                "architect/SE usually need Accela detail or plan-stamp import."
            )
        elif jurisdiction.system == "accela" and jurisdiction.crawlable:
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
                    "Portals change often — use City of Boulder open-data sync for volume, "
                    "or import key permits with architect/SE manually."
                )
            )
        elif jurisdiction.system == "energov":
            run.status = "manual"
            run.message = (
                f"{jurisdiction.name} EnerGov CSS is not bulk-exported. "
                f"For City of Boulder use open-data sync. Portal: "
                f"{jurisdiction.search_url or jurisdiction.portal_url}"
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


async def sync_all_crawlable(
    db: Session,
    max_results: int = 30,
    since: str = "2023-01-01",
) -> list[PermitSyncRun]:
    runs = []
    # Prefer high-value open data first
    if get_jurisdiction("city_of_boulder"):
        runs.append(
            await sync_jurisdiction(
                db, "city_of_boulder", max_results=max(max_results, 1500), since=since
            )
        )
    for jurisdiction in list_jurisdictions():
        if jurisdiction.crawlable and jurisdiction.id != "city_of_boulder":
            runs.append(await sync_jurisdiction(db, jurisdiction.id, max_results=max_results, since=since))
    return runs


def seed_sample_permits(db: Session) -> dict:
    """Seed realistic sample rows so market research UI is usable offline."""
    samples = [
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2026-01482",
            "permit_type": "Building Permit - Single Family Detached Dwelling",
            "work_type": "Addition",
            "status": "Issued",
            "description": "Two-story addition with foundation and structural framing. Structural plans uploaded. Architect: Coburn Architecture. Structural engineer: Jordan Hale PE-54321 Front Range Structural.",
            "address": "1234 Mapleton Ave",
            "city": "Boulder",
            "issued_at": "2026-03-12",
            "estimated_value": 485000,
            "contractor_name": "BC Builders LLC",
            "has_structural_plans": True,
            "architect_firm": "Coburn Architecture",
            "structural_engineer_name": "Jordan Hale",
            "structural_engineer_license": "PE-54321",
            "structural_engineer_firm": "Front Range Structural",
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2025-08821",
            "permit_type": "Building Permit - Multifamily",
            "status": "Issued",
            "description": "Interior alteration combining units; selective structural opening.",
            "address": "1900 Folsom St",
            "city": "Boulder",
            "issued_at": "2025-11-02",
            "estimated_value": 104876,
            "contractor_name": "Rob Luckett Builders",
            "architect_firm": "Studio H Architecture",
            "has_structural_plans": True,
            "structural_engineer_name": "Alex Rivera",
            "structural_engineer_license": "PE-11882",
            "structural_engineer_firm": "Rivera Structural",
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-ACC2026-00018",
            "permit_type": "Building Permit - Accessory",
            "status": "Issued",
            "description": "24x44 garage/shop with engineered foundation.",
            "address": "812 Cornell Ave",
            "city": "Boulder",
            "issued_at": "2026-01-18",
            "estimated_value": 210179,
            "contractor_name": "Pearl Construction LLC",
            "architect_firm": "Coburn Architecture",
            "has_structural_plans": True,
            "structural_engineer_name": "Jordan Hale",
            "structural_engineer_firm": "Front Range Structural",
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2025-04110",
            "permit_type": "Building Permit - Single Family Detached Dwelling",
            "status": "Issued",
            "description": "New ADU with foundation and structural framing.",
            "address": "455 Arapahoe Ave",
            "city": "Boulder",
            "issued_at": "2025-06-20",
            "estimated_value": 320000,
            "contractor_name": "BC Builders LLC",
            "architect_firm": "Coburn Architecture",
            "has_structural_plans": True,
            "structural_engineer_firm": "Front Range Structural",
            "structural_engineer_name": "Jordan Hale",
        },
        {
            "jurisdiction_id": "boulder_county",
            "permit_number": "BP-26-0120",
            "permit_type": "New Residence",
            "status": "Issued",
            "description": "New single-family residence. Engineered foundation required.",
            "address": "8800 N 95th St",
            "city": "Longmont",
            "issued_at": "2026-02-01",
            "estimated_value": 1250000,
            "contractor_name": "Boulder Creek Builders LLC",
            "architect_firm": "Arch11",
            "has_structural_plans": True,
            "structural_engineer_name": "Alex Rivera",
            "structural_engineer_license": "PE-11882",
            "structural_engineer_firm": "Rivera Structural",
        },
        {
            "jurisdiction_id": "longmont",
            "permit_number": "BLD-26-3341",
            "permit_type": "Commercial Remodel",
            "status": "Under Review",
            "description": "Tenant finish with selective structural opening in bearing wall.",
            "address": "455 Main St",
            "city": "Longmont",
            "issued_at": "2026-04-08",
            "estimated_value": 275000,
            "contractor_name": "Van Matre Construction LLC",
            "architect_firm": "Studio H Architecture",
            "has_structural_plans": True,
            "structural_engineer_name": "Sam Okonkwo",
            "structural_engineer_firm": "Ok Structural LLC",
        },
        {
            "jurisdiction_id": "louisville",
            "permit_number": "RES-26-077",
            "permit_type": "Foundation Repair",
            "status": "Issued",
            "description": "Helical pier foundation repair — engineered design required.",
            "address": "912 Centennial Dr",
            "city": "Louisville",
            "issued_at": "2026-05-11",
            "estimated_value": 48000,
            "contractor_name": "All Phase Restoration",
            "has_structural_plans": True,
            "structural_engineer_name": "Casey Nguyen",
            "structural_engineer_firm": "Nguyen Engineering",
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2026-00901",
            "permit_type": "Building Permit - Single Family Detached Dwelling",
            "status": "Issued",
            "description": "Kitchen remodel, non-structural. No structural plans required.",
            "address": "210 Pearl St",
            "city": "Boulder",
            "issued_at": "2026-01-05",
            "estimated_value": 62000,
            "contractor_name": "Lifetime Windows",
            "has_structural_plans": False,
        },
        {
            "jurisdiction_id": "city_of_boulder",
            "permit_number": "BLD-2024-12001",
            "permit_type": "Building Permit - Commercial",
            "status": "Issued",
            "description": "Core/shell TI with new steel moment frame. Architect: Arch11.",
            "address": "1600 38th St",
            "city": "Boulder",
            "issued_at": "2024-09-14",
            "estimated_value": 2100000,
            "contractor_name": "Boulder Creek Builders LLC",
            "architect_firm": "Arch11",
            "has_structural_plans": True,
            "structural_engineer_firm": "Rivera Structural",
            "structural_engineer_name": "Alex Rivera",
        },
    ]
    return import_manual_permits(db, samples)
