"""Jurisdiction registry for Boulder County area building permit portals."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Jurisdiction:
    id: str
    name: str
    kind: str  # city | county | town
    system: str  # accela | energov | mygov | other
    portal_url: str
    search_url: str | None = None
    notes: str = ""
    crawlable: bool = False


JURISDICTIONS: dict[str, Jurisdiction] = {
    "boulder_county": Jurisdiction(
        id="boulder_county",
        name="Boulder County (unincorporated)",
        kind="county",
        system="accela",
        portal_url="https://aca-prod.accela.com/BOCO/Welcome.aspx",
        search_url="https://aca-prod.accela.com/BOCO/Cap/CapHome.aspx?module=Building&TabName=Building",
        notes="Accela Citizen Access. Search Building Permits; licensed professionals often listed on record detail.",
        crawlable=True,
    ),
    "city_of_boulder": Jurisdiction(
        id="city_of_boulder",
        name="City of Boulder",
        kind="city",
        system="opendata",
        portal_url="https://energovcss.bouldercolorado.gov/EnerGov_Prod/SelfService/BoulderCO_Prod",
        search_url="https://open-data.bouldercolorado.gov/datasets/e3ff6248e4a547bcba31025d2c5c9fee_0/about",
        notes=(
            "Best bulk source: City Construction Permits open data (contractor + EstProjectCost). "
            "EnerGov CSS still used for case detail; architect/SE rarely in open data."
        ),
        crawlable=True,
    ),
    "longmont": Jurisdiction(
        id="longmont",
        name="City of Longmont",
        kind="city",
        system="accela",
        portal_url="https://aca-prod.accela.com/LONGMONT/Default.aspx",
        search_url="https://aca-prod.accela.com/LONGMONT/Cap/CapHome.aspx?module=Building&TabName=Home",
        notes="Accela Citizen Access — Building module.",
        crawlable=True,
    ),
    "louisville": Jurisdiction(
        id="louisville",
        name="City of Louisville",
        kind="city",
        system="energov",
        portal_url="https://www.louisvilleco.gov/local-government/government/departments/building-safety/css-online-portal",
        search_url=None,
        notes="EnerGov Customer Self Service (CSS). Manual review for now.",
        crawlable=False,
    ),
    "lafayette": Jurisdiction(
        id="lafayette",
        name="City of Lafayette",
        kind="city",
        system="mygov",
        portal_url="https://www.lafayetteco.gov/",
        search_url=None,
        notes="MyGov / email submittals. Manual review for now.",
        crawlable=False,
    ),
    "superior": Jurisdiction(
        id="superior",
        name="Town of Superior",
        kind="town",
        system="other",
        portal_url="https://www.superiorcolorado.gov/",
        notes="Check town building department portal.",
        crawlable=False,
    ),
    "erie": Jurisdiction(
        id="erie",
        name="Town of Erie",
        kind="town",
        system="other",
        portal_url="https://www.erieco.gov/",
        notes="Partially in Boulder County — include when address falls in Boulder County.",
        crawlable=False,
    ),
    "nederland": Jurisdiction(
        id="nederland",
        name="Town of Nederland",
        kind="town",
        system="other",
        portal_url="https://nederlandco.org/",
        crawlable=False,
    ),
    "lyons": Jurisdiction(
        id="lyons",
        name="Town of Lyons",
        kind="town",
        system="other",
        portal_url="https://www.townoflyons.com/",
        crawlable=False,
    ),
}


def list_jurisdictions() -> list[Jurisdiction]:
    return list(JURISDICTIONS.values())


def get_jurisdiction(jurisdiction_id: str) -> Jurisdiction | None:
    return JURISDICTIONS.get(jurisdiction_id)
