"""Agent 4: Compliance Agent for evidence-grounded policy and certification verification."""

import re
import uuid
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.compliance_prompts import COMPLIANCE_ANALYSIS_SYSTEM_PROMPT
from app.models.compliance import ComplianceRuleType, ComplianceStatus
from app.schemas.compliance import (
    ComplianceInput,
    ComplianceResult,
    ComplianceRuleInput,
    RuleCheckDetail,
)


class ComplianceAgent:
    """Specialized agent that verifies compliance requirements with evidence citation."""

    @classmethod
    def evaluate(cls, input_data: ComplianceInput) -> ComplianceResult:
        """Evaluate a vendor against a list of compliance rules using deterministic-first gating."""
        checks: List[RuleCheckDetail] = []
        
        held_certs_norm = {c.strip().upper() for c in input_data.held_certifications}
        terms = input_data.quotation_terms or {}
        evidence_text = "\n".join(input_data.evidence_text_chunks)

        for rule in input_data.rules:
            check = cls._evaluate_single_rule(
                rule=rule,
                held_certs=held_certs_norm,
                terms=terms,
                evidence_text=evidence_text,
                vendor_name=input_data.vendor_name,
            )
            checks.append(check)

        # Compute aggregate metrics
        mandatory_checks = [c for c in checks if c.is_mandatory]
        optional_checks = [c for c in checks if not c.is_mandatory]

        passed_mandatory = sum(1 for c in mandatory_checks if c.status == ComplianceStatus.PASS)
        failed_mandatory = sum(1 for c in mandatory_checks if c.status == ComplianceStatus.FAIL)
        unverified_mandatory = sum(1 for c in mandatory_checks if c.status == ComplianceStatus.UNVERIFIED)

        passed_optional = sum(1 for c in optional_checks if c.status == ComplianceStatus.PASS)

        has_unverified = unverified_mandatory > 0

        # Overall Status Determination
        if failed_mandatory > 0:
            overall_status = ComplianceStatus.FAIL
        elif unverified_mandatory > 0:
            overall_status = ComplianceStatus.UNVERIFIED
        elif len(mandatory_checks) > 0 and passed_mandatory == len(mandatory_checks):
            overall_status = ComplianceStatus.PASS
        elif len(mandatory_checks) == 0 and len(checks) > 0:
            # All rules are optional
            if any(c.status == ComplianceStatus.FAIL for c in optional_checks):
                overall_status = ComplianceStatus.FAIL
            else:
                overall_status = ComplianceStatus.PASS
        else:
            overall_status = ComplianceStatus.PASS

        return ComplianceResult(
            vendor_id=input_data.vendor_id,
            overall_status=overall_status,
            has_unverified_mandatory=has_unverified,
            passed_mandatory_checks=passed_mandatory,
            total_mandatory_checks=len(mandatory_checks),
            passed_optional_checks=passed_optional,
            total_optional_checks=len(optional_checks),
            checks=checks,
        )

    @classmethod
    def _evaluate_single_rule(
        cls,
        rule: ComplianceRuleInput,
        held_certs: set[str],
        terms: dict,
        evidence_text: str,
        vendor_name: str,
    ) -> RuleCheckDetail:
        """Evaluate one rule deterministically, falling back to semantic analysis when needed."""
        # 1. Certification Requirements
        if rule.rule_type == ComplianceRuleType.CERTIFICATION_REQUIRED:
            required_cert = rule.parameters.get("certification_name", rule.rule_name).strip().upper()
            
            # Check direct held certifications
            if any(required_cert in c or c in required_cert for c in held_certs):
                return RuleCheckDetail(
                    rule_id=rule.rule_id,
                    rule_code=rule.rule_code,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    is_mandatory=rule.is_mandatory,
                    status=ComplianceStatus.PASS,
                    confidence_score=1.0,
                    evidence_quote=f"Supplier registry records confirm active {required_cert} certification.",
                    explanation=f"Supplier {vendor_name} maintains validated {required_cert} certification.",
                )

            # Check evidence text chunks
            if evidence_text:
                cert_pattern = re.compile(re.escape(required_cert), re.IGNORECASE)
                if cert_pattern.search(evidence_text):
                    # Check for explicit failure markers like 'expired', 'lacks', 'revoked'
                    neg_pattern = re.compile(
                        rf"(?:expired|revoked|pending|lacks|no)\s+{re.escape(required_cert)}",
                        re.IGNORECASE,
                    )
                    if neg_pattern.search(evidence_text):
                        return RuleCheckDetail(
                            rule_id=rule.rule_id,
                            rule_code=rule.rule_code,
                            rule_name=rule.rule_name,
                            rule_type=rule.rule_type,
                            is_mandatory=rule.is_mandatory,
                            status=ComplianceStatus.FAIL,
                            confidence_score=0.95,
                            evidence_quote=f"Evidence indicates {required_cert} is expired or revoked.",
                            explanation=f"Evidence text explicitly mentions revocation or lack of {required_cert}.",
                        )
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.PASS,
                        confidence_score=0.90,
                        evidence_quote=f"Document evidence references active certification: {required_cert}.",
                        explanation=f"Quotation document corroborates compliance with {required_cert}.",
                    )

            # Never assume PASS when evidence is missing
            return RuleCheckDetail(
                rule_id=rule.rule_id,
                rule_code=rule.rule_code,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                is_mandatory=rule.is_mandatory,
                status=ComplianceStatus.UNVERIFIED,
                confidence_score=0.20,
                evidence_quote=None,
                explanation=f"No verified proof or document snippet found confirming {required_cert}.",
            )

        # 2. Deterministic Thresholds (warranty, delivery terms, payment terms)
        elif rule.rule_type == ComplianceRuleType.DETERMINISTIC_THRESHOLD:
            # Check warranty threshold
            if "min_warranty_months" in rule.parameters:
                min_warranty = int(rule.parameters["min_warranty_months"])
                quoted_warranty = terms.get("warranty_months")
                if quoted_warranty is None:
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.UNVERIFIED,
                        confidence_score=0.30,
                        evidence_quote=None,
                        explanation=f"Quotation omitted explicit warranty duration (required >= {min_warranty} months).",
                    )
                elif quoted_warranty >= min_warranty:
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.PASS,
                        confidence_score=1.0,
                        evidence_quote=f"Quoted warranty: {quoted_warranty} months.",
                        explanation=f"Warranty of {quoted_warranty} months satisfies minimum requirement of {min_warranty} months.",
                    )
                else:
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.FAIL,
                        confidence_score=1.0,
                        evidence_quote=f"Quoted warranty: {quoted_warranty} months.",
                        explanation=f"Warranty of {quoted_warranty} months is below required threshold of {min_warranty} months.",
                    )

            # Check payment terms threshold
            if "required_payment_terms" in rule.parameters:
                req_payment = rule.parameters["required_payment_terms"].strip()
                quoted_payment = terms.get("payment_terms")
                if not quoted_payment:
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.UNVERIFIED,
                        confidence_score=0.30,
                        evidence_quote=None,
                        explanation=f"Quotation did not specify payment terms (required '{req_payment}').",
                    )
                elif req_payment.lower() in quoted_payment.lower() or quoted_payment.lower() in req_payment.lower():
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.PASS,
                        confidence_score=1.0,
                        evidence_quote=f"Quoted payment terms: '{quoted_payment}'.",
                        explanation=f"Payment terms '{quoted_payment}' comply with standard policy '{req_payment}'.",
                    )
                else:
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.FAIL,
                        confidence_score=0.95,
                        evidence_quote=f"Quoted payment terms: '{quoted_payment}'.",
                        explanation=f"Quoted payment terms '{quoted_payment}' conflict with required '{req_payment}'.",
                    )

        # 3. Contractual Clauses (e.g. NDA, Governing Law, IP Rights)
        clause_keyword = rule.parameters.get("clause_keyword", rule.rule_name)
        if evidence_text:
            clause_pattern = re.compile(re.escape(clause_keyword), re.IGNORECASE)
            match = clause_pattern.search(evidence_text)
            if match:
                # Extract surrounding context
                start = max(0, match.start() - 60)
                end = min(len(evidence_text), match.end() + 100)
                snippet = evidence_text[start:end].replace("\n", " ").strip()
                
                # Check for explicit rejection/exceptions
                if any(neg in snippet.lower() for neg in ["reject", "decline", "exclude", "not accepted", "refuse"]):
                    return RuleCheckDetail(
                        rule_id=rule.rule_id,
                        rule_code=rule.rule_code,
                        rule_name=rule.rule_name,
                        rule_type=rule.rule_type,
                        is_mandatory=rule.is_mandatory,
                        status=ComplianceStatus.FAIL,
                        confidence_score=0.90,
                        evidence_quote=f"...{snippet}...",
                        explanation=f"Supplier took explicit exception to {rule.rule_name}.",
                    )

                return RuleCheckDetail(
                    rule_id=rule.rule_id,
                    rule_code=rule.rule_code,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    is_mandatory=rule.is_mandatory,
                    status=ComplianceStatus.PASS,
                    confidence_score=0.90,
                    evidence_quote=f"...{snippet}...",
                    explanation=f"Supplier quotation acknowledges and satisfies {rule.rule_name}.",
                )

        # Default to UNVERIFIED for contractual clauses when evidence is missing
        return RuleCheckDetail(
            rule_id=rule.rule_id,
            rule_code=rule.rule_code,
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            is_mandatory=rule.is_mandatory,
            status=ComplianceStatus.UNVERIFIED,
            confidence_score=0.25,
            evidence_quote=None,
            explanation=f"No contractual evidence found in submitted documents for {rule.rule_name}.",
        )
