"""City of Boulder Construction Permits open data (ArcGIS FeatureServer).

This is the richest bulk public source for contractor names and estimated
project cost in Boulder. Architect / structural engineer of record are usually
not published in this layer — those come from Accela detail pages or manual
import of plan stamps.
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx

from app.services.permit_accela import ScrapedPermit
from app.services.permit_structural import (
    detect_structural_signals,
    extract_architect_from_text,
    extract_engineer_from_text,
    parse_money,
)

FEATURE_SERVER = (
    "https://services.arcgis.com/ePKBjXrBZ2vEEgWd/arcgis/rest/services/"
    "Construction_Permits/FeatureServer/0/query"
)
SOURCE_URL = (
    "https://open-data.bouldercolorado.gov/datasets/"
    "e3ff6248e4a547bcba31025d2c5c9fee_0/about"
)
USER_AGENT = "PersonalAssistantMarketResearch/0.1 (+local; open-data sync)"

# Prefer building / structural-leaning work over mechanical/plumbing noise.
DEFAULT_WHERE = (
    "("
    "PermitType LIKE '%Building%' OR "
    "PermitType LIKE '%Construction%' OR "
    "PermitWorkType LIKE '%Structural%' OR "
    "Description LIKE '%structural%' OR "
    "Description LIKE '%foundation%'"
    ")"
)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], fmt)
        except ValueError:
            continue
    return None


def _attrs_to_scraped(attrs: dict) -> ScrapedPermit | None:
    permit_number = (attrs.get("PermitNum") or "").strip()
    if not permit_number:
        return None

    permit_type = attrs.get("PermitType")
    work_type = attrs.get("PermitWorkType")
    description = attrs.get("Description") or attrs.get("ProjectName")
    blob = " ".join(filter(None, [permit_type, work_type, description]))
    has_structural, signals = detect_structural_signals(permit_type, description, work_type)
    engineer = extract_engineer_from_text(blob)
    architect = extract_architect_from_text(blob)
    amount = parse_money(attrs.get("EstProjectCost"))
    contractor = (attrs.get("ContractorCompanyName") or "").strip() or None
    if contractor and contractor.upper() in {
        "WAITING FOR LICENSED CONTRACTOR",
        "OWNER",
        "N/A",
        "NA",
        "NONE",
    }:
        contractor = None

    external_id = (attrs.get("PermitID") or permit_number).strip()
    city = (attrs.get("OriginalCity") or "Boulder").strip() or "Boulder"
    address = (attrs.get("OriginalAddress") or "").strip() or None

    return ScrapedPermit(
        external_id=external_id,
        permit_number=permit_number,
        permit_type=permit_type,
        work_type=work_type,
        status=attrs.get("StatusCurrent"),
        description=(description or "")[:2000] or None,
        address=address,
        city=city,
        applied_at=_parse_date(attrs.get("AppliedDate")),
        issued_at=_parse_date(attrs.get("IssuedDate")),
        estimated_value=str(attrs.get("EstProjectCost")) if attrs.get("EstProjectCost") is not None else None,
        estimated_value_amount=amount,
        contractor_name=contractor,
        contractor_trade=(attrs.get("ContractorTrade") or None),
        architect_name=architect["name"],
        architect_firm=architect["firm"],
        structural_engineer_name=engineer["name"],
        structural_engineer_license=engineer["license"],
        structural_engineer_firm=engineer["firm"],
        has_structural_plans=has_structural,
        structural_signals=signals,
        source_url=SOURCE_URL,
        raw_snippet=json.dumps(attrs)[:2000],
    )


class BoulderOpenDataClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    async def fetch_building_permits(
        self,
        *,
        since: str = "2023-01-01",
        max_records: int = 2500,
        page_size: int = 500,
        building_only: bool = True,
    ) -> list[ScrapedPermit]:
        """Pull recent City of Boulder construction permits from open data."""
        where = DEFAULT_WHERE if building_only else "1=1"
        if since:
            where = f"({where}) AND (IssuedDate >= '{since}' OR AppliedDate >= '{since}')"

        out_fields = ",".join(
            [
                "PermitID",
                "PermitNum",
                "Description",
                "AppliedDate",
                "IssuedDate",
                "StatusCurrent",
                "OriginalAddress",
                "OriginalCity",
                "ProjectName",
                "PermitType",
                "PermitWorkType",
                "EstProjectCost",
                "ContractorCompanyName",
                "ContractorTrade",
            ]
        )

        results: list[ScrapedPermit] = []
        offset = 0
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        ) as client:
            while len(results) < max_records:
                batch = min(page_size, max_records - len(results))
                response = await client.get(
                    FEATURE_SERVER,
                    params={
                        "where": where,
                        "outFields": out_fields,
                        "orderByFields": "IssuedDate DESC",
                        "resultOffset": offset,
                        "resultRecordCount": batch,
                        "f": "json",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("error"):
                    raise RuntimeError(str(payload["error"]))
                features = payload.get("features") or []
                if not features:
                    break
                for feature in features:
                    scraped = _attrs_to_scraped(feature.get("attributes") or {})
                    if scraped:
                        results.append(scraped)
                if len(features) < batch:
                    break
                offset += len(features)
                if not payload.get("exceededTransferLimit"):
                    # ArcGIS sets this when more pages exist; if absent, we may still
                    # have more — continue until an empty page.
                    if len(features) < page_size:
                        break

        return results
