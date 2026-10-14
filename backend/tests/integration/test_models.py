"""Integration tests for database domain models, relationships, and tenant isolation."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import (
    Base,
    Organization,
    User,
    UserRole,
    Vendor,
    VendorStatus,
    VendorPerformanceHistory,
    ProcurementRequest,
    ProcurementRequestItem,
    RequestStatus,
    RequestPriority,
    Quotation,
    QuotationLineItem,
    ComplianceRule,
    ComplianceRuleType,
    ComplianceStatus,
    ComplianceCheck,
    RiskAssessment,
    RiskTier,
    ScoringPolicy,
    Evaluation,
    EvaluationStatus,
    VendorScore,
    ScenarioEvaluation,
    ScenarioStatus,
    ApprovalRecord,
    ApprovalAction,
    AuditEvent,
    AuditAction,
)
from app.core.database import set_current_tenant, with_tenant_filter


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide a clean in-memory async SQLite database session for model testing."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_organization_and_user_creation(db_session: AsyncSession):
    """Verify organization and user creation with RBAC roles."""
    org = Organization(
        name="Acme Aerospace",
        slug="acme-aerospace",
        domain="acme.com",
        settings={"default_currency": "USD"},
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        organization_id=org.id,
        email="procurement.head@acme.com",
        hashed_password="secure_hash_string",
        full_name="Jane Doe",
        role=UserRole.PROCUREMENT_MANAGER,
    )
    db_session.add(user)
    await db_session.commit()

    # Query back
    result = await db_session.execute(select(User).where(User.email == "procurement.head@acme.com"))
    fetched_user = result.scalar_one()
    assert fetched_user.full_name == "Jane Doe"
    assert fetched_user.role == UserRole.PROCUREMENT_MANAGER
    assert fetched_user.organization.name == "Acme Aerospace"


@pytest.mark.asyncio
async def test_vendor_and_performance_history(db_session: AsyncSession):
    """Verify vendor profile and operational history metrics."""
    org = Organization(name="Tech Corp", slug="tech-corp")
    db_session.add(org)
    await db_session.flush()

    vendor = Vendor(
        organization_id=org.id,
        name="Apex Titanium Ltd",
        country="DE",
        status=VendorStatus.VERIFIED,
        tax_id="DE-99887766",
        metadata_info={"certifications": ["ISO-9001", "AS9100D"]},
    )
    db_session.add(vendor)
    await db_session.flush()

    perf = VendorPerformanceHistory(
        organization_id=org.id,
        vendor_id=vendor.id,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        defect_rate=Decimal("0.0085"), # 0.85%
        on_time_delivery_rate=Decimal("0.9920"), # 99.2%
        historical_orders_count=45,
        total_spend=Decimal("1250000.5000"),
    )
    db_session.add(perf)
    await db_session.commit()

    # Verification
    result = await db_session.execute(select(Vendor).where(Vendor.id == vendor.id))
    fetched_vendor = result.scalar_one()
    assert len(fetched_vendor.performance_records) == 1
    assert fetched_vendor.performance_records[0].defect_rate == Decimal("0.0085")
    assert fetched_vendor.performance_records[0].total_spend == Decimal("1250000.5000")


@pytest.mark.asyncio
async def test_procurement_request_with_items(db_session: AsyncSession):
    """Verify procurement request header and line items with cascading relationships."""
    org = Organization(name="Global Manufacturing", slug="global-mfg")
    db_session.add(org)
    await db_session.flush()

    user = User(
        organization_id=org.id,
        email="buyer@global.com",
        hashed_password="hash",
        full_name="John Smith",
        role=UserRole.PROCUREMENT_MANAGER,
    )
    db_session.add(user)
    await db_session.flush()

    req = ProcurementRequest(
        organization_id=org.id,
        requester_id=user.id,
        title="Turbine Casing Material Sourcing",
        description="High-grade titanium alloy casings required for Q3 production",
        budget_ceiling=Decimal("500000.0000"),
        currency="USD",
        target_delivery_date=date(2026, 9, 30),
        status=RequestStatus.UNDER_EVALUATION,
        priority=RequestPriority.HIGH,
    )
    req.items.append(
        ProcurementRequestItem(
            item_code="TC-900",
            description="Grade 5 Titanium Casing Assembly",
            quantity=Decimal("150.0000"),
            unit_of_measure="units",
            target_unit_price=Decimal("3200.0000"),
            technical_specs={"tensile_strength_mpa": 895, "density_g_cm3": 4.43},
            mandatory_certifications=["ISO-9001", "RoHS"],
        )
    )
    db_session.add(req)
    await db_session.commit()

    result = await db_session.execute(select(ProcurementRequest).where(ProcurementRequest.id == req.id))
    fetched_req = result.scalar_one()
    assert len(fetched_req.items) == 1
    assert fetched_req.items[0].quantity == Decimal("150.0000")
    assert fetched_req.items[0].technical_specs["tensile_strength_mpa"] == 895


@pytest.mark.asyncio
async def test_quotation_decimal_precision(db_session: AsyncSession):
    """Verify monetary precision and avoidance of floating-point drift."""
    org = Organization(name="Aerospace Corp", slug="aero-corp")
    db_session.add(org)
    await db_session.flush()

    user = User(
        organization_id=org.id,
        email="mgr@aero.com",
        hashed_password="hash",
        full_name="Procurement Officer",
    )
    db_session.add(user)
    await db_session.flush()

    req = ProcurementRequest(
        organization_id=org.id,
        requester_id=user.id,
        title="Industrial Sensors",
        description="Laser telemetry sensors",
        budget_ceiling=Decimal("100000.0000"),
        target_delivery_date=date(2026, 12, 1),
    )
    vendor = Vendor(organization_id=org.id, name="Optics Tech Gmbh", country="DE")
    db_session.add_all([req, vendor])
    await db_session.flush()

    quote = Quotation(
        organization_id=org.id,
        request_id=req.id,
        vendor_id=vendor.id,
        quote_reference="QT-DE-2026-009",
        currency="USD",
        base_price=Decimal("85000.5000"),
        freight_cost=Decimal("2500.2500"),
        tax_amount=Decimal("4375.0000"),
        discount_amount=Decimal("1875.7500"),
        total_quote_amount=Decimal("90000.0000"),
        quoted_delivery_date=date(2026, 11, 15),
        payment_terms="Net 45",
        incoterms="DDP",
        warranty_months=24,
    )
    db_session.add(quote)
    await db_session.commit()

    result = await db_session.execute(select(Quotation).where(Quotation.id == quote.id))
    fetched_quote = result.scalar_one()
    assert fetched_quote.base_price == Decimal("85000.5000")
    assert fetched_quote.freight_cost == Decimal("2500.2500")
    assert fetched_quote.discount_amount == Decimal("1875.7500")
    assert fetched_quote.payment_terms == "Net 45"


@pytest.mark.asyncio
async def test_evaluation_and_scoring_policy(db_session: AsyncSession):
    """Verify evaluation snapshot storage, scoring policies, and vendor scores."""
    org = Organization(name="Energy Systems", slug="energy-sys")
    db_session.add(org)
    await db_session.flush()

    user = User(organization_id=org.id, email="eval@energy.com", hashed_password="hash", full_name="Eval User")
    db_session.add(user)
    await db_session.flush()

    req = ProcurementRequest(
        organization_id=org.id,
        requester_id=user.id,
        title="Solar Panels",
        description="High efficiency monocrystalline panels",
        budget_ceiling=Decimal("300000.0000"),
        target_delivery_date=date(2026, 10, 1),
    )
    policy = ScoringPolicy(
        organization_id=org.id,
        name="Standard Direct Sourcing Policy v1",
        version=1,
        cost_weight=Decimal("0.3500"),
        quality_weight=Decimal("0.2500"),
        delivery_weight=Decimal("0.2000"),
        compliance_weight=Decimal("0.1000"),
        risk_weight=Decimal("0.0500"),
        terms_weight=Decimal("0.0500"),
    )
    db_session.add_all([req, policy])
    await db_session.flush()

    vendor = Vendor(organization_id=org.id, name="Solaris Corp")
    db_session.add(vendor)
    await db_session.flush()

    eval_record = Evaluation(
        organization_id=org.id,
        request_id=req.id,
        scoring_policy_id=policy.id,
        status=EvaluationStatus.EVALUATING,
        thread_id="thread-eval-9901",
        input_hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        spec_snapshot={"title": "Solar Panels", "budget": 300000},
        policy_snapshot={"cost_weight": 0.35, "quality_weight": 0.25},
        is_immutable=False,
    )
    db_session.add(eval_record)
    await db_session.flush()

    score = VendorScore(
        evaluation_id=eval_record.id,
        vendor_id=vendor.id,
        rank=1,
        is_eligible=True,
        overall_score=Decimal("88.4500"),
        landed_cost_score=Decimal("92.0000"),
        quality_score=Decimal("85.0000"),
        delivery_score=Decimal("90.0000"),
        compliance_score=Decimal("100.0000"),
        risk_score=Decimal("80.0000"),
        terms_score=Decimal("75.0000"),
        landed_cost_calculated=Decimal("284500.0000"),
        criterion_breakdowns={"cost_breakdown": {"unit_price": 284.50}},
    )
    db_session.add(score)
    await db_session.commit()

    result = await db_session.execute(select(Evaluation).where(Evaluation.id == eval_record.id))
    fetched_eval = result.scalar_one()
    assert fetched_eval.scores[0].rank == 1
    assert fetched_eval.scores[0].overall_score == Decimal("88.4500")
    assert fetched_eval.policy_snapshot["cost_weight"] == 0.35


@pytest.mark.asyncio
async def test_tenant_isolation_filter(db_session: AsyncSession):
    """Verify tenant isolation query helper strictly filters cross-tenant records."""
    org_a = Organization(name="Tenant Alpha", slug="tenant-alpha")
    org_b = Organization(name="Tenant Beta", slug="tenant-beta")
    db_session.add_all([org_a, org_b])
    await db_session.flush()

    v_a = Vendor(organization_id=org_a.id, name="Vendor for Alpha")
    v_b = Vendor(organization_id=org_b.id, name="Vendor for Beta")
    db_session.add_all([v_a, v_b])
    await db_session.commit()

    # Query with tenant filter for Org A
    stmt_a = with_tenant_filter(select(Vendor), Vendor, tenant_id=org_a.id)
    res_a = await db_session.execute(stmt_a)
    vendors_a = res_a.scalars().all()
    assert len(vendors_a) == 1
    assert vendors_a[0].name == "Vendor for Alpha"

    # Query with tenant filter for Org B
    stmt_b = with_tenant_filter(select(Vendor), Vendor, tenant_id=org_b.id)
    res_b = await db_session.execute(stmt_b)
    vendors_b = res_b.scalars().all()
    assert len(vendors_b) == 1
    assert vendors_b[0].name == "Vendor for Beta"
