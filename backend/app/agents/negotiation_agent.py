"""Agent 6: Negotiation Simulation Agent with deterministic bounds validation."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.negotiation_prompts import NEGOTIATION_SIMULATION_SYSTEM_PROMPT
from app.schemas.negotiation import (
    NegotiationRound,
    NegotiationSimInput,
    NegotiationSimResult,
)


class NegotiationSimulationAgent:
    """Specialized agent simulating vendor counteroffers, concessions, and trade-off frontiers."""

    @classmethod
    def simulate(cls, input_data: NegotiationSimInput) -> NegotiationSimResult:
        """Simulate multi-round negotiation counteroffers bounded by vendor cost floor."""
        cost_floor_price = (
            input_data.quoted_base_price * (input_data.cost_floor_pct / Decimal("100.00"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        target_discount_pct = input_data.target_price_discount_pct
        target_price = (
            input_data.quoted_base_price * (Decimal("1.00") - (target_discount_pct / Decimal("100.00")))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Context message for LLM
        prompt_context = (
            f"Vendor: {input_data.vendor_name}\n"
            f"Original Quoted Price: ${input_data.quoted_base_price:,.2f}\n"
            f"Vendor Cost Floor Percentage: {input_data.cost_floor_pct}%\n"
            f"Minimum Allowed Price (Cost Floor): ${cost_floor_price:,.2f}\n"
            f"Buyer Target Discount: {target_discount_pct}%\n"
            f"Buyer Target Price: ${target_price:,.2f}\n"
            f"Vendor Concession Elasticity: {input_data.vendor_elasticity_score}\n"
            f"Payment Terms: {input_data.quoted_payment_terms} (Target: {input_data.target_payment_terms})\n"
            f"Warranty: {input_data.quoted_warranty_months} months\n"
        )

        messages = [
            SystemMessage(content=NEGOTIATION_SIMULATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt_context),
        ]

        def fallback_simulator() -> NegotiationSimResult:
            """Pure mathematical concession simulator strictly honoring bounds."""
            elasticity = Decimal(str(max(0.1, min(1.0, input_data.vendor_elasticity_score))))

            # Recommended opening offer (aggressive anchor: 1.3x target discount, bounded by floor)
            opening_discount_pct = min(target_discount_pct * Decimal("1.3"), Decimal("25.00"))
            raw_opening = input_data.quoted_base_price * (Decimal("1.00") - (opening_discount_pct / Decimal("100.00")))
            opening_price = max(cost_floor_price, raw_opening).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Round 1: Defensive vendor response
            r1_concession = ((input_data.quoted_base_price - opening_price) * Decimal("0.25") * elasticity)
            r1_counter = (input_data.quoted_base_price - r1_concession).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            round_1 = NegotiationRound(
                round_number=1,
                buyer_offer_price=opening_price,
                vendor_counter_price=r1_counter,
                vendor_concessions=[f"Offered minor introductory price concession of ${r1_concession:,.2f}."],
                vendor_withheld=["Refused extended payment terms; insisted on Net 30."],
                concession_rationale="Initial defensive position citing raw material input costs and margin constraints.",
            )

            # Round 2: Buyer compromises, Vendor grants payment terms
            r2_buyer_offer = (opening_price + ((r1_counter - opening_price) * Decimal("0.40"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            r2_concession = ((r1_counter - r2_buyer_offer) * Decimal("0.40") * elasticity)
            r2_counter = max(cost_floor_price, (r1_counter - r2_concession)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            round_2 = NegotiationRound(
                round_number=2,
                buyer_offer_price=r2_buyer_offer,
                vendor_counter_price=r2_counter,
                vendor_concessions=[
                    f"Additional price reduction to ${r2_counter:,.2f}.",
                    f"Agreed to move towards {input_data.target_payment_terms or 'Net 45'} on condition of milestone sign-off.",
                ],
                vendor_withheld=["Refused extended 36-month warranty without added service fee."],
                concession_rationale="Supplier yielded on cash flow terms to preserve high-margin volume commitment.",
            )

            # Round 3: Settlement Landing Zone
            r3_buyer_offer = (r2_buyer_offer + ((r2_counter - r2_buyer_offer) * Decimal("0.50"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            final_concession = ((r2_counter - r3_buyer_offer) * Decimal("0.50") * elasticity)
            expected_final = max(cost_floor_price, (r2_counter - final_concession)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            round_3 = NegotiationRound(
                round_number=3,
                buyer_offer_price=r3_buyer_offer,
                vendor_counter_price=expected_final,
                vendor_concessions=[
                    f"Final negotiated pricing confirmed at ${expected_final:,.2f}.",
                    "Included free expedited shipping on first production batch.",
                ],
                vendor_withheld=["Final non-negotiable floor reached; further cuts rejected."],
                concession_rationale="Supplier stabilized deal at minimum acceptable hurdle rate.",
            )

            savings_amount = (input_data.quoted_base_price - expected_final).quantize(Decimal("0.01"))
            savings_pct = (
                (savings_amount / input_data.quoted_base_price) * Decimal("100.00")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            leverage = "STRONG" if elasticity > Decimal("0.7") else "MODERATE" if elasticity > Decimal("0.4") else "WEAK"

            recommendations = [
                f"Anchor opening bid at ${opening_price:,.2f} ({opening_discount_pct:.1f}% below quote).",
                f"Pair price demands with concession trades (e.g. {input_data.target_payment_terms or 'Net 60'}).",
                f"Do not negotiate below walkaway threshold of ${cost_floor_price:,.2f}.",
            ]

            risk = (
                "Low risk of supplier walkout within projected range. Exceeding cost floor "
                f"(${cost_floor_price:,.2f}) risks vendor refusal or quality compromises."
            )

            return NegotiationSimResult(
                vendor_id=input_data.vendor_id,
                vendor_name=input_data.vendor_name,
                rounds=[round_1, round_2, round_3],
                recommended_opening_price=opening_price,
                walkaway_price=cost_floor_price,
                expected_final_price=expected_final,
                projected_savings_amount=savings_amount,
                projected_savings_pct=savings_pct,
                negotiation_leverage=leverage,
                tactical_recommendations=recommendations,
                risk_assessment=risk,
                is_hypothetical_simulation=True,
            )

        result = llm_provider.generate_structured(
            messages=messages,
            response_model=NegotiationSimResult,
            fallback_factory=fallback_simulator,
        )

        # Deterministic bounds validation post-processor
        return cls._enforce_bounds(result, cost_floor_price, input_data.quoted_base_price, fallback_simulator)

    @classmethod
    def _enforce_bounds(
        cls,
        result: NegotiationSimResult,
        cost_floor: Decimal,
        original_price: Decimal,
        fallback_factory,
    ) -> NegotiationSimResult:
        """Enforce strict physical invariant: simulated price cannot be below cost floor or above quote."""
        result.is_hypothetical_simulation = True

        if result.expected_final_price < cost_floor or result.expected_final_price > original_price:
            # Revert to mathematically guaranteed fallback
            return fallback_factory()

        return result
