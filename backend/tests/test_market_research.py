from datetime import datetime

from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app
from app.services.permit_structural import extract_architect_from_text, parse_money
from app.services.permit_sync import seed_sample_permits


def test_parse_money_and_architect():
    assert parse_money("$1,234.50") == 1234.5
    assert parse_money(None) is None
    arch = extract_architect_from_text("Architect: Coburn Architecture designed the addition.")
    assert arch["firm"] and "Coburn" in arch["firm"]


def test_seed_and_market_research_endpoint():
    init_db()
    db = SessionLocal()
    try:
        seed_sample_permits(db)
    finally:
        db.close()

    with TestClient(app) as client:
        report = client.get("/api/permits/market-research?months=60").json()
        assert report["permit_count"] >= 5
        assert report["total_estimated_value"] > 0
        assert report["contractors"]
        top = report["contractors"][0]
        assert top["job_count"] >= 1
        assert "name" in top
        # Sample data includes architect / SE pairings
        assert report["with_architect"] >= 1
        assert report["with_engineer"] >= 1
        assert report["contractor_architect_pairs"]


def test_boulder_opendata_fetch_smoke():
    """Live open-data pull — skip soft-fail if network blocks ArcGIS."""
    import asyncio

    from app.services.permit_boulder_opendata import BoulderOpenDataClient

    async def run():
        client = BoulderOpenDataClient(timeout=45)
        return await client.fetch_building_permits(since="2025-01-01", max_records=25, page_size=25)

    try:
        rows = asyncio.run(run())
    except Exception as exc:  # network / egress
        print("opendata skip:", exc)
        return

    assert len(rows) > 0
    assert any(r.contractor_name for r in rows)
    assert any(r.estimated_value_amount for r in rows)
