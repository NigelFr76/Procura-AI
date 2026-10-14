"""Deterministic eligibility gating service for non-negotiable procurement constraints."""

from decimal import Decimal
from typing import List, Tuple
from app.schemas.scoring import (
    VendorQuotationInput,
    VendorComplianceInput,
    ProcurementRequirementsInput,
)


class EligibilityEvaluator:
    """Evaluates strict, non-negotiable eligibility gates before comparative scoring."""

    @classmethod
    def evaluate(
        cls,
        quote: VendorQuotationInput,
        compliance: VendorComplianceInput,
        requirements: ProcurementRequirementsInput,
        calculated_landed_cost: Decimal,
    ) -> Tuple[bool, List[str]]:
        """Determine whether a vendor meets 100% of non-negotiable procurement conditions.
        
        Returns:
            Tuple of (is_eligible, list_of_violations)
        """
        violations: List[str] = []

        # Gate 1: Budget Ceiling
        if calculated_landed_cost > requirements.budget_ceiling:
            violations.append(
                f"Landed cost {calculated_landed_cost:,.2f} {requirements.currency} "
                f"exceeds budget ceiling of {requirements.budget_ceiling:,.2f} {requirements.currency}"
            )

        # Gate 2: Delivery Deadline
        deadline = requirements.max_acceptable_delivery_date or requirements.target_delivery_date
        if quote.quoted_delivery_date > deadline:
            violations.append(
                f"Quoted delivery date {quote.quoted_delivery_date} exceeds "
                f"mandatory delivery deadline {deadline}"
            )

        # Gate 3: Mandatory Certifications
        if requirements.required_certifications:
            held_certs = {c.strip().upper() for c in compliance.certifications_held}
            for req_cert in requirements.required_certifications:
                if req_cert.strip().upper() not in held_certs:
                    violations.append(f"Missing mandatory certification: {req_cert}")

        # Gate 4: Unverified Mandatory Compliance
        if compliance.has_unverified_mandatory:
            violations.append("Mandatory compliance verification is incomplete or unverified")
        elif compliance.total_mandatory_checks > 0 and compliance.passed_mandatory_checks < compliance.total_mandatory_checks:
            failed_count = compliance.total_mandatory_checks - compliance.passed_mandatory_checks
            violations.append(f"Failed {failed_count} mandatory compliance checks")

        is_eligible = len(violations) == 0
        return is_eligible, violations
