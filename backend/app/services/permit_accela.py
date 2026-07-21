"""Best-effort Accela Citizen Access search for building permits.

Accela portals are ASP.NET apps without a stable public JSON API for anonymous
search. This adapter fetches CapHome search pages and CapDetail pages, then
parses HTML for permit numbers, addresses, status, and licensed professionals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from urllib.parse import urljoin

import httpx

from app.services.permit_jurisdictions import Jurisdiction
from app.services.permit_structural import (
    detect_structural_signals,
    extract_architect_from_text,
    extract_engineer_from_text,
    parse_money,
)

USER_AGENT = "PersonalAssistantPermitWatch/0.1 (+local; respectful crawl)"

RESULT_ROW_RE = re.compile(
    r'<a[^>]+href="([^"]*CapDetail\.aspx\?[^"]+)"[^>]*>\s*([^<]+?)\s*</a>',
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


@dataclass
class ScrapedPermit:
    external_id: str
    permit_number: str
    permit_type: str | None = None
    work_type: str | None = None
    status: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    applied_at: datetime | None = None
    issued_at: datetime | None = None
    estimated_value: str | None = None
    estimated_value_amount: float | None = None
    contractor_name: str | None = None
    contractor_trade: str | None = None
    architect_name: str | None = None
    architect_firm: str | None = None
    source_url: str | None = None
    structural_engineer_name: str | None = None
    structural_engineer_license: str | None = None
    structural_engineer_firm: str | None = None
    has_structural_plans: bool = False
    structural_signals: list[str] = field(default_factory=list)
    raw_snippet: str | None = None


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = unescape(TAG_RE.sub(" ", text))
    return WS_RE.sub(" ", text).strip()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(value[:10], fmt)
        except ValueError:
            continue
    return None


class AccelaPermitClient:
    def __init__(self, jurisdiction: Jurisdiction, timeout: float = 30.0) -> None:
        self.jurisdiction = jurisdiction
        self.timeout = timeout
        self.base = jurisdiction.portal_url.rsplit("/", 1)[0] if jurisdiction.portal_url else ""
        # Normalize base to agency root, e.g. https://aca-prod.accela.com/BOCO
        if "/Cap/" in (jurisdiction.search_url or ""):
            self.base = jurisdiction.search_url.split("/Cap/")[0]
        elif jurisdiction.portal_url:
            # Welcome.aspx or Default.aspx
            self.base = jurisdiction.portal_url.rsplit("/", 1)[0]

    async def search_recent_building_permits(self, max_results: int = 40) -> list[ScrapedPermit]:
        """Search Accela CapHome for structural-leaning permit types via global search keywords."""
        if not self.jurisdiction.search_url:
            return []

        keywords = [
            "foundation",
            "structural",
            "New Residence",
            "New Commercial",
            "Addition",
        ]
        found: dict[str, ScrapedPermit] = {}

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        ) as client:
            for keyword in keywords:
                if len(found) >= max_results:
                    break
                batch = await self._global_search(client, keyword, limit=15)
                for item in batch:
                    found[item.external_id] = item

            # Enrich a subset with detail pages for engineer names
            to_enrich = list(found.values())[: min(12, len(found))]
            for item in to_enrich:
                if item.source_url:
                    await self._enrich_from_detail(client, item)

        return list(found.values())[:max_results]

    async def _global_search(
        self, client: httpx.AsyncClient, keyword: str, limit: int = 15
    ) -> list[ScrapedPermit]:
        # Accela global search page pattern used by many ACA tenants
        search_url = f"{self.base}/GlobalSearch/Result.aspx"
        try:
            response = await client.get(
                search_url,
                params={"QueryText": keyword, "Module": "Building"},
            )
        except httpx.HTTPError:
            return []

        if response.status_code >= 400:
            # Fall back: load CapHome and look for any CapDetail links already rendered
            try:
                response = await client.get(self.jurisdiction.search_url or self.base)
            except httpx.HTTPError:
                return []

        html = response.text
        return self._parse_search_html(html, limit=limit)

    def _parse_search_html(self, html: str, limit: int = 15) -> list[ScrapedPermit]:
        results: list[ScrapedPermit] = []
        for match in RESULT_ROW_RE.finditer(html):
            href = unescape(match.group(1))
            label = _clean(match.group(2))
            if not label or len(label) < 3:
                continue
            absolute = urljoin(self.base + "/", href)
            external_id = absolute
            # CapDetail often includes Module=Building&TabName=...&capID1=...
            cap_id_match = re.search(r"capID1=([^&]+).*capID2=([^&]+).*capID3=([^&]+)", href, re.I)
            if cap_id_match:
                external_id = f"{cap_id_match.group(1)}-{cap_id_match.group(2)}-{cap_id_match.group(3)}"

            # Grab a nearby snippet for type/status/address heuristics
            start = max(0, match.start() - 200)
            end = min(len(html), match.end() + 500)
            snippet = _clean(html[start:end])

            has_structural, signals = detect_structural_signals(label, snippet)
            engineer = extract_engineer_from_text(snippet)

            results.append(
                ScrapedPermit(
                    external_id=external_id,
                    permit_number=label.split()[0] if label else label,
                    permit_type=label if " " in label else None,
                    description=snippet[:400] or None,
                    address=self._guess_address(snippet),
                    status=self._guess_status(snippet),
                    source_url=absolute,
                    has_structural_plans=has_structural,
                    structural_signals=signals,
                    structural_engineer_name=engineer["name"],
                    structural_engineer_license=engineer["license"],
                    raw_snippet=snippet[:800],
                )
            )
            if len(results) >= limit:
                break
        return results

    async def _enrich_from_detail(self, client: httpx.AsyncClient, item: ScrapedPermit) -> None:
        if not item.source_url:
            return
        try:
            response = await client.get(item.source_url)
        except httpx.HTTPError:
            return
        if response.status_code >= 400:
            return

        text = _clean(response.text)
        has_structural, signals = detect_structural_signals(
            item.permit_type, item.description, text
        )
        if has_structural:
            item.has_structural_plans = True
            item.structural_signals = list({*item.structural_signals, *signals})

        engineer = extract_engineer_from_text(text)
        if engineer["name"]:
            item.structural_engineer_name = engineer["name"]
        if engineer["license"]:
            item.structural_engineer_license = engineer["license"]
        if engineer["firm"]:
            item.structural_engineer_firm = engineer["firm"]

        architect = extract_architect_from_text(text)
        if architect["name"]:
            item.architect_name = architect["name"]
        if architect["firm"]:
            item.architect_firm = architect["firm"]

        contractor_match = re.search(
            r"(?:Licensed\s+)?Contractor\s*[:\-–]?\s*([A-Z0-9][A-Za-z0-9 &'.,\-]{2,80})",
            text,
            re.I,
        )
        if contractor_match and not item.contractor_name:
            item.contractor_name = contractor_match.group(1).strip()[:200]

        value_match = re.search(
            r"(?:Job\s+Value|Valuation|Estimated\s+Value|Project\s+Cost)\s*[:\-–]?\s*\$?\s*([\d,]+(?:\.\d+)?)",
            text,
            re.I,
        )
        if value_match:
            item.estimated_value = value_match.group(1)
            item.estimated_value_amount = parse_money(value_match.group(1))

        # Look for labeled fields Accela often uses
        for pattern, attr in (
            (r"Record Type\s+([A-Za-z0-9 /\-]+)", "permit_type"),
            (r"Status\s+([A-Za-z0-9 /\-]+)", "status"),
            (r"Project Description\s+(.+?)(?:Related|Professional|Contact|Parcel)", "description"),
        ):
            match = re.search(pattern, text, re.I)
            if match and not getattr(item, attr):
                setattr(item, attr, match.group(1).strip()[:300])

        addr_match = re.search(
            r"(?:Work Location|Address)\s+(\d{1,6}\s+[A-Za-z0-9 .'#\-]+)",
            text,
            re.I,
        )
        if addr_match and not item.address:
            item.address = addr_match.group(1).strip()[:300]

    @staticmethod
    def _guess_address(snippet: str) -> str | None:
        match = re.search(r"\b(\d{1,6}\s+[A-Z][A-Za-z0-9 .'#\-]{3,40})\b", snippet)
        return match.group(1).strip() if match else None

    @staticmethod
    def _guess_status(snippet: str) -> str | None:
        for status in (
            "Issued",
            "In Review",
            "Under Review",
            "Approved",
            "Closed",
            "Expired",
            "Applied",
            "Pending",
        ):
            if status.lower() in snippet.lower():
                return status
        return None
