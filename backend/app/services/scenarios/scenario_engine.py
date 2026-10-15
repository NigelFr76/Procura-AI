"""Domain service for executing What-If scenario simulations against immutable baselines."""

import copy
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional

from app.schemas.scenario import (
    ScenarioParameterOverrides,
    ScenarioRunInput,
    ScenarioRunResult,
    VendorDifferential,
)
from app.schemas.scoring import ScoringPolicyConfig
from app.services.scoring.engine import VendorScoringEngine


class ScenarioSimulationEngine:
    """Stateless pure-Python engine for running what-if parameter shifts without mutating baselines."""

    @classmethod
    def execute_scenario(cls, input_data: ScenarioRunInput) -> ScenarioRunResult:
        """Deep copy baseline, apply parameter overrides, re-score deterministically, and compute differentials."""
        # Step 1: Deep copy baseline structures to guarantee 100% baseline immutability
        requirements = copy.deepcopy(input_data.baseline_requirements)
        quotes = copy.deepcopy(input_data.baseline_quotes)
        performances = copy.deepcopy(input_data.baseline_performances)
        compliances = copy.deepcopy(input_data.baseline_compliances)
        risks = copy.deepcopy(input_data.baseline_risks)
        policy = copy.deepcopy(input_data.baseline_policy)
        baseline_scorecard = input_data.baseline_scorecard

        overrides = input_data.overrides

        # Step 2: Apply parameter overrides to copied state
        # 2a. Budget ceiling override
        if overrides.budget_ceiling_override is not None:
            requirements.budget_ceiling = overrides.budget_ceiling_override

        # 2b. Vendor price overrides
        if overrides.vendor_price_overrides:
            for q in quotes:
                if q.vendor_id in overrides.vendor_price_overrides:
                    q.base_price = overrides.vendor_price_overrides[q.vendor_id]

        # 2c. Vendor delivery date overrides
        if overrides.vendor_delivery_overrides:
            for q in quotes:
                if q.vendor_id in overrides.vendor_delivery_overrides:
                    val = overrides.vendor_delivery_overrides[q.vendor_id]
                    if isinstance(val, str):
                        q.quoted_delivery_date = datetime.strptime(val, "%Y-%m-%d").date()
                    elif isinstance(val, date):
                        q.quoted_delivery_date = val

        # 2d. Vendor certification revocations
        if overrides.vendor_cert_revocations:
            for v_id, revoked_certs in overrides.vendor_cert_revocations.items():
                if v_id in compliances:
                    revoked_norm = {c.strip().upper() for c in revoked_certs}
                    compliances[v_id].certifications_held = [
                        c for c in compliances[v_id].certifications_held
                        if c.strip().upper() not in revoked_norm
                    ]

        # 2e. Policy weight overrides
        if overrides.policy_weight_overrides:
            weight_updates = dict(overrides.policy_weight_overrides)
            current_weights = {
                "cost_weight": policy.cost_weight,
                "quality_weight": policy.quality_weight,
                "delivery_weight": policy.delivery_weight,
                "compliance_weight": policy.compliance_weight,
                "risk_weight": policy.risk_weight,
                "terms_weight": policy.terms_weight,
            }
            current_weights.update(weight_updates)
            
            # Normalize to sum to exactly 1.0000
            total = sum(current_weights.values())
            normalized_weights = {k: (v / total).quantize(Decimal("0.0001")) for k, v in current_weights.items()}
            # Adjust rounding difference on cost_weight
            diff = Decimal("1.0000") - sum(normalized_weights.values())
            normalized_weights["cost_weight"] += diff

            policy = ScoringPolicyConfig(
                policy_id=policy.policy_id,
                name=f"{policy.name} (Simulated Overrides)",
                version=policy.version + 1,
                cost_weight=normalized_weights["cost_weight"],
                quality_weight=normalized_weights["quality_weight"],
                delivery_weight=normalized_weights["delivery_weight"],
                compliance_weight=normalized_weights["compliance_weight"],
                risk_weight=normalized_weights["risk_weight"],
                terms_weight=normalized_weights["terms_weight"],
                tie_breaker_hierarchy=policy.tie_breaker_hierarchy,
            )

        # Step 3: Re-evaluate deterministically with VendorScoringEngine
        scenario_eval_id = uuid.uuid4()
        scenario_scorecard = VendorScoringEngine.evaluate_and_rank(
            evaluation_id=scenario_eval_id,
            requirements=requirements,
            quotes=quotes,
            performances=performances,
            compliances=compliances,
            risks=risks,
            policy=policy,
        )

        # Step 4: Compute vendor differentials
        baseline_scores_by_vendor = {s.vendor_id: s for s in baseline_scorecard.scores}
        differentials: List[VendorDifferential] = []

        for sc_detail in scenario_scorecard.scores:
            base_detail = baseline_scores_by_vendor.get(sc_detail.vendor_id)
            if base_detail:
                rank_delta = base_detail.rank - sc_detail.rank  # Positive = improved rank
                score_delta = sc_detail.overall_score - base_detail.overall_score
                cost_delta = sc_detail.landed_cost_calculated - base_detail.landed_cost_calculated
                elig_shifted = base_detail.is_eligible != sc_detail.is_eligible

                differentials.append(
                    VendorDifferential(
                        vendor_id=sc_detail.vendor_id,
                        vendor_name=sc_detail.vendor_name,
                        baseline_rank=base_detail.rank,
                        scenario_rank=sc_detail.rank,
                        rank_delta=rank_delta,
                        baseline_score=base_detail.overall_score,
                        scenario_score=sc_detail.overall_score,
                        score_delta=score_delta,
                        baseline_landed_cost=base_detail.landed_cost_calculated,
                        scenario_landed_cost=sc_detail.landed_cost_calculated,
                        cost_delta=cost_delta,
                        baseline_eligible=base_detail.is_eligible,
                        scenario_eligible=sc_detail.is_eligible,
                        eligibility_shifted=elig_shifted,
                    )
                )

        # Step 5: Check Winner Displacement
        prev_winner_id = baseline_scorecard.recommended_vendor_id
        prev_winner_name = baseline_scorecard.recommended_vendor_name
        new_winner_id = scenario_scorecard.recommended_vendor_id
        new_winner_name = scenario_scorecard.recommended_vendor_name

        winner_displaced = (
            prev_winner_id is not None
            and new_winner_id is not None
            and prev_winner_id != new_winner_id
        )

        # Step 6: Generate Causal Explanation
        causal_explanation = cls._generate_causal_explanation(
            winner_displaced=winner_displaced,
            prev_winner_name=prev_winner_name,
            new_winner_name=new_winner_name,
            differentials=differentials,
            overrides=overrides,
        )

        return ScenarioRunResult(
            scenario_name=input_data.scenario_name,
            baseline_evaluation_id=input_data.baseline_evaluation_id,
            baseline_input_hash=baseline_scorecard.input_hash,
            baseline_immutable_verified=True,
            winner_displaced=winner_displaced,
            previous_winner_id=prev_winner_id,
            previous_winner_name=prev_winner_name,
            new_winner_id=new_winner_id,
            new_winner_name=new_winner_name,
            vendor_differentials=differentials,
            causal_explanation=causal_explanation,
            scenario_scorecard=scenario_scorecard,
        )

    @classmethod
    def _generate_causal_explanation(
        cls,
        winner_displaced: bool,
        prev_winner_name: Optional[str],
        new_winner_name: Optional[str],
        differentials: List[VendorDifferential],
        overrides: ScenarioParameterOverrides,
    ) -> str:
        """Synthesize clear causal rationale explaining rank shifts or retention."""
        if winner_displaced:
            new_winner_diff = next((d for d in differentials if d.vendor_name == new_winner_name), None)
            prev_winner_diff = next((d for d in differentials if d.vendor_name == prev_winner_name), None)

            explanation = (
                f"WINNER DISPLACEMENT DETECTED: {new_winner_name} displaced previous Rank 1 winner {prev_winner_name}. "
            )

            if new_winner_diff and new_winner_diff.cost_delta < 0:
                explanation += (
                    f"Primary causal factor: Landed cost reduction of ${abs(new_winner_diff.cost_delta):,.2f} "
                    f"boosted score by +{new_winner_diff.score_delta:.2f} pts, overtaking the baseline leader."
                )
            elif prev_winner_diff and not prev_winner_diff.scenario_eligible:
                explanation += (
                    f"Primary causal factor: Previous winner {prev_winner_name} became INELIGIBLE under simulated constraint overrides."
                )
            elif overrides.policy_weight_overrides:
                explanation += (
                    f"Primary causal factor: Shift in evaluation policy criteria weights altered the balance of advantage in favor of {new_winner_name}."
                )
            else:
                explanation += (
                    f"Score gain (+{new_winner_diff.score_delta:.2f} pts) shifted {new_winner_name} from Rank {new_winner_diff.baseline_rank} to Rank 1."
                    if new_winner_diff else ""
                )
            return explanation
        else:
            if prev_winner_name:
                return (
                    f"RANKING STABILITY CONFIRMED: Baseline winner {prev_winner_name} maintains Rank 1 position. "
                    f"Simulated parameter shifts were insufficient to alter the top supplier recommendation."
                )
            return "No eligible winner was recommended in baseline or scenario evaluation."
