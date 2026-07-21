"""Aggregate permit records into competitor / market research views."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

from sqlalchemy.orm import Session

from app.models import BuildingPermit


def _parse_amount(permit: BuildingPermit) -> float:
    if permit.estimated_value_amount is not None:
        return float(permit.estimated_value_amount)
    if permit.estimated_value:
        try:
            return float(str(permit.estimated_value).replace(",", "").replace("$", ""))
        except ValueError:
            return 0.0
    return 0.0


def _months_span(dates: list[datetime]) -> float:
    usable = [d for d in dates if d]
    if len(usable) < 2:
        return 1.0
    span_days = (max(usable) - min(usable)).days
    return max(span_days / 30.437, 1.0)


def _filtered_query(
    db: Session,
    *,
    jurisdiction_id: str | None,
    since: datetime | None,
    structural_only: bool,
    q: str | None,
):
    query = db.query(BuildingPermit)
    if jurisdiction_id:
        query = query.filter(BuildingPermit.jurisdiction_id == jurisdiction_id)
    if structural_only:
        query = query.filter(BuildingPermit.has_structural_plans.is_(True))
    if since:
        query = query.filter(
            (BuildingPermit.issued_at >= since) | (BuildingPermit.applied_at >= since)
        )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (BuildingPermit.contractor_name.ilike(like))
            | (BuildingPermit.architect_name.ilike(like))
            | (BuildingPermit.architect_firm.ilike(like))
            | (BuildingPermit.structural_engineer_name.ilike(like))
            | (BuildingPermit.structural_engineer_firm.ilike(like))
            | (BuildingPermit.permit_number.ilike(like))
            | (BuildingPermit.address.ilike(like))
            | (BuildingPermit.description.ilike(like))
        )
    return query


def build_market_research(
    db: Session,
    *,
    jurisdiction_id: str | None = None,
    months: int = 24,
    structural_only: bool = False,
    q: str | None = None,
    limit: int = 40,
) -> dict:
    since = datetime.utcnow() - timedelta(days=max(months, 1) * 30)
    permits = _filtered_query(
        db,
        jurisdiction_id=jurisdiction_id,
        since=since,
        structural_only=structural_only,
        q=q,
    ).all()

    total_value = 0.0
    with_contractor = 0
    with_architect = 0
    with_engineer = 0
    structural_count = 0

    contractors: dict[str, dict] = defaultdict(
        lambda: {
            "name": "",
            "job_count": 0,
            "total_value": 0.0,
            "values": [],
            "dates": [],
            "jurisdictions": set(),
            "architects": set(),
            "engineers": set(),
            "recent_permits": [],
        }
    )
    architects: dict[str, dict] = defaultdict(
        lambda: {
            "name": "",
            "job_count": 0,
            "total_value": 0.0,
            "contractors": set(),
            "engineers": set(),
            "dates": [],
        }
    )
    engineers: dict[str, dict] = defaultdict(
        lambda: {
            "name": "",
            "job_count": 0,
            "total_value": 0.0,
            "contractors": set(),
            "architects": set(),
            "dates": [],
            "firm": None,
        }
    )
    pairings: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"contractor": "", "architect": "", "job_count": 0, "total_value": 0.0}
    )

    for permit in permits:
        amount = _parse_amount(permit)
        total_value += amount
        when = permit.issued_at or permit.applied_at
        if permit.has_structural_plans:
            structural_count += 1

        contractor = (permit.contractor_name or "").strip()
        architect = (permit.architect_firm or permit.architect_name or "").strip()
        engineer = (permit.structural_engineer_firm or permit.structural_engineer_name or "").strip()

        if contractor:
            with_contractor += 1
            key = contractor.upper()
            row = contractors[key]
            row["name"] = contractor
            row["job_count"] += 1
            row["total_value"] += amount
            row["values"].append(amount)
            if when:
                row["dates"].append(when)
            row["jurisdictions"].add(permit.jurisdiction_id)
            if architect:
                row["architects"].add(architect)
            if engineer:
                row["engineers"].add(engineer)
            if len(row["recent_permits"]) < 5:
                row["recent_permits"].append(
                    {
                        "permit_number": permit.permit_number,
                        "address": permit.address,
                        "city": permit.city,
                        "estimated_value_amount": amount or None,
                        "issued_at": when.isoformat() if when else None,
                        "permit_type": permit.permit_type,
                    }
                )

        if architect:
            with_architect += 1
            akey = architect.upper()
            arow = architects[akey]
            arow["name"] = architect
            arow["job_count"] += 1
            arow["total_value"] += amount
            if when:
                arow["dates"].append(when)
            if contractor:
                arow["contractors"].add(contractor)
            if engineer:
                arow["engineers"].add(engineer)

        if engineer:
            with_engineer += 1
            ekey = engineer.upper()
            erow = engineers[ekey]
            erow["name"] = engineer
            erow["firm"] = permit.structural_engineer_firm
            erow["job_count"] += 1
            erow["total_value"] += amount
            if when:
                erow["dates"].append(when)
            if contractor:
                erow["contractors"].add(contractor)
            if architect:
                erow["architects"].add(architect)

        if contractor and architect:
            pkey = (contractor.upper(), architect.upper())
            prow = pairings[pkey]
            prow["contractor"] = contractor
            prow["architect"] = architect
            prow["job_count"] += 1
            prow["total_value"] += amount

    def rank_contractors() -> list[dict]:
        ranked = []
        for row in contractors.values():
            months_active = _months_span(row["dates"])
            ranked.append(
                {
                    "name": row["name"],
                    "job_count": row["job_count"],
                    "total_value": round(row["total_value"], 2),
                    "avg_job_value": round(row["total_value"] / row["job_count"], 2)
                    if row["job_count"]
                    else 0,
                    "median_job_value": round(median(row["values"]), 2) if row["values"] else 0,
                    "jobs_per_month": round(row["job_count"] / months_active, 2),
                    "jurisdictions": sorted(row["jurisdictions"]),
                    "top_architects": sorted(row["architects"])[:8],
                    "top_engineers": sorted(row["engineers"])[:8],
                    "recent_permits": row["recent_permits"],
                }
            )
        ranked.sort(key=lambda r: (r["total_value"], r["job_count"]), reverse=True)
        return ranked[:limit]

    def rank_people(bucket: dict) -> list[dict]:
        ranked = []
        for row in bucket.values():
            months_active = _months_span(row["dates"])
            item = {
                "name": row["name"],
                "job_count": row["job_count"],
                "total_value": round(row["total_value"], 2),
                "jobs_per_month": round(row["job_count"] / months_active, 2),
                "top_contractors": sorted(row.get("contractors", set()))[:8],
            }
            if "engineers" in row:
                item["top_engineers"] = sorted(row["engineers"])[:8]
            if "architects" in row:
                item["top_architects"] = sorted(row["architects"])[:8]
            if row.get("firm"):
                item["firm"] = row["firm"]
            ranked.append(item)
        ranked.sort(key=lambda r: (r["job_count"], r["total_value"]), reverse=True)
        return ranked[:limit]

    pairing_list = sorted(
        (
            {
                "contractor": p["contractor"],
                "architect": p["architect"],
                "job_count": p["job_count"],
                "total_value": round(p["total_value"], 2),
            }
            for p in pairings.values()
        ),
        key=lambda r: (r["job_count"], r["total_value"]),
        reverse=True,
    )[:limit]

    return {
        "window_months": months,
        "since": since.isoformat(),
        "permit_count": len(permits),
        "structural_count": structural_count,
        "total_estimated_value": round(total_value, 2),
        "with_contractor": with_contractor,
        "with_architect": with_architect,
        "with_engineer": with_engineer,
        "coverage": {
            "contractor_pct": round(100 * with_contractor / len(permits), 1) if permits else 0,
            "architect_pct": round(100 * with_architect / len(permits), 1) if permits else 0,
            "engineer_pct": round(100 * with_engineer / len(permits), 1) if permits else 0,
        },
        "contractors": rank_contractors(),
        "architects": rank_people(architects),
        "engineers": rank_people(engineers),
        "contractor_architect_pairs": pairing_list,
        "notes": [
            "City of Boulder open data is strongest for contractor names and job value.",
            "Architect and structural engineer of record are often only on plan stamps / Accela detail — coverage will be lower until those are enriched or imported.",
            "Assessor permit CSVs have value but usually no design professionals.",
        ],
    }
