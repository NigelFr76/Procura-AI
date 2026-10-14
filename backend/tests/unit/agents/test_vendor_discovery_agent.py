"""Unit tests for Agent 2: Vendor Discovery Agent."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base, Organization, Vendor, VendorStatus
from app.agents.vendor_discovery_agent import VendorDiscoveryAgent
from app.schemas.spec import ProcurementSpecification
from app.schemas.vendor_discovery import VendorDiscoveryInput


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide isolated async SQLite database session for agent tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_vendor_discovery_shortlisting(db_session: AsyncSession):
    """Verify registry search, capability scoring, and audit of exclusions."""
    org = Organization(name="Airbus Prime", slug="airbus-prime")
    db_session.add(org)
    await db_session.flush()

    # Vendor 1: Verified with ISO-9001 (should be shortlisted)
    v1 = Vendor(
        organization_id=org.id,
        name="Precision Alloys Gmbh",
        country="DE",
        status=VendorStatus.VERIFIED,
        metadata_info={"certifications": ["ISO-9001", "AS9100"]},
    )
    # Vendor 2: Missing required ISO-9001 (should be excluded)
    v2 = Vendor(
        organization_id=org.id,
        name="Budget Castings Co",
        country="US",
        status=VendorStatus.SHORTLISTED,
        metadata_info={"certifications": ["RoHS"]},
    )
    # Vendor 3: Suspended (should be excluded immediately)
    v3 = Vendor(
        organization_id=org.id,
        name="Defunct Supplies Ltd",
        country="UK",
        status=VendorStatus.SUSPENDED,
        metadata_info={"certifications": ["ISO-9001"]},
    )
    db_session.add_all([v1, v2, v3])
    await db_session.commit()

    spec = ProcurementSpecification(
        title="Titanium Casing Sourcing",
        description="High grade titanium casings",
        required_certifications=["ISO-9001"],
    )
    discovery_input = VendorDiscoveryInput(spec=spec, organization_id=org.id, max_shortlist=5)

    result = await VendorDiscoveryAgent.discover_and_shortlist(db_session, discovery_input)

    assert result.total_registry_scanned == 3
    assert len(result.shortlisted) == 1
    assert result.shortlisted[0].vendor_name == "Precision Alloys Gmbh"
    assert result.shortlisted[0].is_verified is True
    assert result.shortlisted[0].match_score >= 0.90

    # Excluded vendors should include v2 and v3 with reasons
    excluded_names = {e.vendor_name for e in result.excluded}
    assert "Budget Castings Co" in excluded_names
    assert "Defunct Supplies Ltd" in excluded_names
