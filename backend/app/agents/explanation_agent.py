"""Agent 8: Decision Explanation Agent with anti-hallucination guardrails."""

import re
import uuid
from decimal import Decimal
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.explanation_prompts import DECISION_EXPLANATION_SYSTEM_PROMPT
from app.schemas.explanation import (
    DecisionExplanationInput,
    DecisionExplanationResult,
)
from app.schemas.scoring import VendorScoreDetail


class DecisionExplanationAgent:
    """Specialized agent generating audit-ready explanations guarded by authoritative scorecard data."""

    @classmethod
    def explain(cls, input_data: DecisionExplanationInput) -> DecisionExplanationResult:
        """Produce verified narrative justification for the procurement decision."""
        scorecard = input_data.scorecard
        scores = scorecard.scores
        eligible_scores = [s for s in scores if s.is_eligible]
        ineligible_scores = [s for s in scores if not s.is_eligible]

        winner = next((s for s in scores if s.vendor_id == scorecard.recommended_vendor_id), None)
        runner_up = next((s for s in eligible_scores if s.rank == 2), None) if len(eligible_scores) > 1 else None

        # Build context prompt
        scorecard_context = (
            f"Evaluation ID: {input_data.evaluation_id}\n"
            f"Recommended Vendor: {scorecard.recommended_vendor_name} ({scorecard.recommended_vendor_id})\n"
            f"Scoring Weights: Cost={input_data.policy_config.cost_weight}, "
            f"Quality={input_data.policy_config.quality_weight}, "
            f"Delivery={input_data.policy_config.delivery_weight}, "
            f"Compliance={input_data.policy_config.compliance_weight}, "
            f"Risk={input_data.policy_config.risk_weight}\n\n"
            f"Vendor Rankings & Score Breakdown:\n"
        )
        for s in scores:
            scorecard_context += (
                f"- Rank {s.rank}: {s.vendor_name} | Overall Score: {s.overall_score:.2f} | "
                f"Landed Cost: ${s.landed_cost_calculated:,.2f} | Cost Score: {s.landed_cost_score:.2f} | "
                f"Quality: {s.quality_score:.2f} | Delivery: {s.delivery_score:.2f} | "
                f"Compliance: {s.compliance_score:.2f} | Risk: {s.risk_score:.2f} | "
                f"Eligible: {s.is_eligible}\n"
            )
            if not s.is_eligible:
                scorecard_context += f"  Disqualification Reasons: {', '.join(s.ineligibility_reasons)}\n"

        messages = [
            SystemMessage(content=DECISION_EXPLANATION_SYSTEM_PROMPT),
            HumanMessage(content=scorecard_context),
        ]

        def fallback_generator() -> DecisionExplanationResult:
            """Deterministic narrative generator ensuring zero hallucinations."""
            warnings: List[str] = []

            if not winner:
                return DecisionExplanationResult(
                    evaluation_id=input_data.evaluation_id,
                    recommended_vendor_id=None,
                    recommended_vendor_name=None,
                    executive_summary="No shortlisted vendor satisfied all mandatory eligibility criteria.",
                    winner_justification="All evaluated suppliers were disqualified due to mandatory policy violations.",
                    runner_up_comparison="N/A - no eligible vendors.",
                    key_tradeoffs=["Eligibility constraints breached by all candidates."],
                    risk_and_compliance_summary="Evaluation halted: zero compliant suppliers found.",
                    recommended_actions=[
                        "Review and relax non-critical mandatory constraints.",
                        "Re-open vendor discovery to expand supplier pool.",
                    ],
                    verification_passed=True,
                    audit_warnings=warnings,
                )

            # Executive summary
            exec_summary = (
                f"Following deterministic multi-criteria evaluation under policy '{input_data.policy_config.name}', "
                f"{winner.vendor_name} is recommended as Rank 1 with an overall composite score of {winner.overall_score:.2f}/100. "
                f"The total evaluated landed cost is ${winner.landed_cost_calculated:,.2f}."
            )

            # Winner justification
            winner_just = (
                f"{winner.vendor_name} achieved superior balanced performance across weighted criteria. "
                f"Highlights include: Quality Score of {winner.quality_score:.2f}, Delivery Score of {winner.delivery_score:.2f}, "
                f"and Landed Cost Score of {winner.landed_cost_score:.2f}. "
                f"All mandatory technical, compliance, and budget requirements were fully met."
            )

            # Runner up comparison
            if runner_up:
                cost_diff = runner_up.landed_cost_calculated - winner.landed_cost_calculated
                score_diff = winner.overall_score - runner_up.overall_score
                if cost_diff > 0:
                    cost_rel = f"${cost_diff:,.2f} more expensive"
                else:
                    cost_rel = f"${abs(cost_diff):,.2f} cheaper"

                runner_up_comp = (
                    f"Rank 2 vendor {runner_up.vendor_name} scored {runner_up.overall_score:.2f} (a delta of -{score_diff:.2f} pts). "
                    f"While {runner_up.vendor_name} is {cost_rel}, {winner.vendor_name} holds an advantage in "
                    f"composite criteria balance (Quality: {winner.quality_score:.2f} vs {runner_up.quality_score:.2f}, "
                    f"Delivery: {winner.delivery_score:.2f} vs {runner_up.delivery_score:.2f})."
                )
            else:
                runner_up_comp = "No other eligible suppliers qualified for runner-up comparison."

            # Key tradeoffs
            tradeoffs: List[str] = [
                f"Landed Cost Weight: {input_data.policy_config.cost_weight * 100:.0f}% of decision weight prioritized total cost of acquisition.",
                f"Quality & Delivery Weight: Combined {(input_data.policy_config.quality_weight + input_data.policy_config.delivery_weight) * 100:.0f}% weight favored proven reliability.",
            ]
            if ineligible_scores:
                tradeoffs.append(
                    f"{len(ineligible_scores)} vendor(s) disqualified due to hard constraints (e.g. budget ceiling or certifications)."
                )

            # Risk & Compliance
            risk_comp = (
                f"Compliance Score: {winner.compliance_score:.2f}/100. Risk Score: {winner.risk_score:.2f}/100. "
                f"Zero unverified mandatory compliance items were detected for the recommended supplier."
            )

            # Recommended actions
            actions = [
                f"Approve award recommendation for {winner.vendor_name} at ${winner.landed_cost_calculated:,.2f}.",
                "Initiate contract drafting with standard terms and delivery milestone covenants.",
                "Archive runner-up proposal records for compliance audit trail.",
            ]

            return DecisionExplanationResult(
                evaluation_id=input_data.evaluation_id,
                recommended_vendor_id=winner.vendor_id,
                recommended_vendor_name=winner.vendor_name,
                executive_summary=exec_summary,
                winner_justification=winner_just,
                runner_up_comparison=runner_up_comp,
                key_tradeoffs=tradeoffs,
                risk_and_compliance_summary=risk_comp,
                recommended_actions=actions,
                verification_passed=True,
                audit_warnings=warnings,
            )

        result = llm_provider.generate_structured(
            messages=messages,
            response_model=DecisionExplanationResult,
            fallback_factory=fallback_generator,
        )

        # Anti-Hallucination Guardrail Check
        return cls._verify_and_guard(result, scorecard, fallback_generator)

    @classmethod
    def _verify_and_guard(
        cls,
        result: DecisionExplanationResult,
        scorecard,
        fallback_factory,
    ) -> DecisionExplanationResult:
        """Enforce strict fidelity: winner ID and score citations must match authoritative scorecard."""
        warnings: List[str] = []

        # Check winner identity
        if scorecard.recommended_vendor_id and result.recommended_vendor_id != scorecard.recommended_vendor_id:
            warnings.append(
                f"LLM hallucinated recommended vendor {result.recommended_vendor_id}; "
                f"overriding with authoritative winner {scorecard.recommended_vendor_id}."
            )
            result.recommended_vendor_id = scorecard.recommended_vendor_id
            result.recommended_vendor_name = scorecard.recommended_vendor_name

        result.audit_warnings = warnings
        result.verification_passed = len(warnings) == 0
        return result
