"""Unit tests for Agent 4: Compliance Agent."""

import uuid
from app.agents.compliance_agent import ComplianceAgent
from app.models.compliance import ComplianceRuleType, ComplianceStatus
from app.schemas.compliance import ComplianceInput, ComplianceRuleInput


def test_compliance_agent_all_rules_pass():
    """Verify that a vendor meeting all certification and threshold criteria passes."""
    rule1 = ComplianceRuleInput(
        rule_id=uuid.uuid4(),
        rule_code="CERT-ISO9001",
        rule_name="ISO 9001 Quality Management",
        rule_type=ComplianceRuleType.CERTIFICATION_REQUIRED,
        is_mandatory=True,
        parameters={"certification_name": "ISO 9001"},
    )
    rule2 = ComplianceRuleInput(
        rule_id=uuid.uuid4(),
        rule_code="THRES-WARRANTY",
        rule_name="Minimum 12 Months Warranty",
        rule_type=ComplianceRuleType.DETERMINISTIC_THRESHOLD,
        is_mandatory=True,
        parameters={"min_warranty_months": 12},
    )
    rule3 = ComplianceRuleInput(
        rule_id=uuid.uuid4(),
        rule_code="CLAUSE-NDA",
        rule_name="Mutual Non-Disclosure Agreement",
        rule_type=ComplianceRuleType.CONTRACTUAL_CLAUSE,
        is_mandatory=False,
        parameters={"clause_keyword": "Non-Disclosure Agreement"},
    )

    compliance_input = ComplianceInput(
        vendor_id=uuid.uuid4(),
        vendor_name="AeroTech Precision Ltd",
        rules=[rule1, rule2, rule3],
        held_certifications=["ISO 9001:2015", "AS9100D"],
        quotation_terms={"warranty_months": 24, "payment_terms": "Net 30"},
        evidence_text_chunks=[
            "Section 8: Supplier hereby agrees to all terms of the Mutual Non-Disclosure Agreement."
        ],
    )

    result = ComplianceAgent.evaluate(compliance_input)

    assert result.overall_status == ComplianceStatus.PASS
    assert result.has_unverified_mandatory is False
    assert result.passed_mandatory_checks == 2
    assert result.total_mandatory_checks == 2
    assert result.passed_optional_checks == 1
    assert result.total_optional_checks == 1
    assert len(result.checks) == 3


def test_compliance_agent_unverified_mandatory():
    """Verify that missing proof for a mandatory certification defaults strictly to UNVERIFIED."""
    rule = ComplianceRuleInput(
        rule_id=uuid.uuid4(),
        rule_code="CERT-AS9100",
        rule_name="AS9100 Aerospace Certification",
        rule_type=ComplianceRuleType.CERTIFICATION_REQUIRED,
        is_mandatory=True,
        parameters={"certification_name": "AS9100"},
    )

    compliance_input = ComplianceInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Titan Castings Inc",
        rules=[rule],
        held_certifications=["ISO 9001"],  # Lacks AS9100
        quotation_terms={},
        evidence_text_chunks=[],
    )

    result = ComplianceAgent.evaluate(compliance_input)

    assert result.overall_status == ComplianceStatus.UNVERIFIED
    assert result.has_unverified_mandatory is True
    assert result.passed_mandatory_checks == 0
    assert result.checks[0].status == ComplianceStatus.UNVERIFIED


def test_compliance_agent_deterministic_threshold_fail():
    """Verify that failing a deterministic parameter threshold produces FAIL."""
    rule = ComplianceRuleInput(
        rule_id=uuid.uuid4(),
        rule_code="THRES-WARRANTY",
        rule_name="Minimum 12 Months Warranty",
        rule_type=ComplianceRuleType.DETERMINISTIC_THRESHOLD,
        is_mandatory=True,
        parameters={"min_warranty_months": 12},
    )

    compliance_input = ComplianceInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Budget Parts Co",
        rules=[rule],
        held_certifications=[],
        quotation_terms={"warranty_months": 6},  # 6 < 12
        evidence_text_chunks=[],
    )

    result = ComplianceAgent.evaluate(compliance_input)

    assert result.overall_status == ComplianceStatus.FAIL
    assert result.passed_mandatory_checks == 0
    assert result.checks[0].status == ComplianceStatus.FAIL
