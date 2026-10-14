"""Stateless criterion normalization services with bounded mathematical algorithms."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple


class CriterionNormalizer:
    """Standardizes heterogeneous procurement criteria into bounded [0.0000 - 100.0000] scale."""

    @classmethod
    def normalize_cost(
        cls,
        cost: Decimal,
        min_cost: Decimal,
        max_cost: Decimal,
        budget_ceiling: Decimal,
    ) -> Decimal:
        """Normalize landed cost (lower cost is strictly better).
        
        Handles identical bids, single vendor, and clamp bounds.
        """
        if cost <= Decimal("0.0000"):
            return Decimal("0.0000")

        # Edge case: all vendors submitted identical landed cost
        if max_cost == min_cost:
            if cost <= budget_ceiling:
                return Decimal("100.0000")
            # Over budget
            ratio = (budget_ceiling / cost) * Decimal("100.0000")
            return max(Decimal("0.0000"), min(Decimal("100.0000"), ratio)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # Standard linear inverse interpolation: (max - current) / (max - min) * 100
        score = ((max_cost - cost) / (max_cost - min_cost)) * Decimal("100.0000")
        score = max(Decimal("0.0000"), min(Decimal("100.0000"), score))
        return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def normalize_delivery(
        cls,
        quoted_date: date,
        target_date: date,
        max_acceptable_date: Optional[date] = None,
    ) -> Decimal:
        """Normalize delivery lead time (earlier is better)."""
        if quoted_date <= target_date:
            return Decimal("100.0000")

        limit_date = max_acceptable_date or target_date
        if quoted_date > limit_date:
            return Decimal("0.0000")

        total_allowed_delay = (limit_date - target_date).days
        if total_allowed_delay <= 0:
            return Decimal("0.0000")

        delay_days = (quoted_date - target_date).days
        penalty_ratio = Decimal(str(delay_days)) / Decimal(str(total_allowed_delay))
        score = (Decimal("1.0000") - penalty_ratio) * Decimal("100.0000")
        score = max(Decimal("0.0000"), min(Decimal("100.0000"), score))
        return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def normalize_quality(
        cls,
        defect_rate: Decimal,
        on_time_rate: Decimal,
        historical_orders_count: int,
    ) -> Decimal:
        """Normalize historical quality and defect metrics."""
        # Baseline score for new vendors without historical orders
        if historical_orders_count == 0:
            return Decimal("70.0000")

        # Defect rate: 0.0000 (0%) -> 100 pts; 0.0500 (5%) or higher -> 0 pts
        defect_penalty = defect_rate * Decimal("2000.0000")
        defect_score = max(Decimal("0.0000"), Decimal("100.0000") - defect_penalty)

        # On-time delivery rate: 1.0000 (100%) -> 100 pts
        on_time_score = on_time_rate * Decimal("100.0000")

        # Weighted blend: 60% defect rate, 40% on-time delivery
        composite = (defect_score * Decimal("0.6000")) + (on_time_score * Decimal("0.4000"))
        composite = max(Decimal("0.0000"), min(Decimal("100.0000"), composite))
        return composite.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def normalize_compliance(
        cls,
        has_unverified_mandatory: bool,
        passed_mandatory: int,
        total_mandatory: int,
        passed_optional: int,
        total_optional: int,
    ) -> Decimal:
        """Normalize compliance check results."""
        if has_unverified_mandatory or passed_mandatory < total_mandatory:
            return Decimal("0.0000")

        # Base 80 points for satisfying all mandatory compliance rules
        score = Decimal("80.0000")
        if total_optional > 0:
            optional_bonus = (Decimal(str(passed_optional)) / Decimal(str(total_optional))) * Decimal("20.0000")
            score += optional_bonus
        else:
            score += Decimal("20.0000")

        return score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def normalize_risk(
        cls,
        composite_risk_score: Decimal,
        uncertainty_score: Decimal,
    ) -> Tuple[Decimal, Decimal]:
        """Normalize risk (lower risk factor produces higher score).
        
        Returns:
            Tuple of (normalized_risk_score, confidence_penalty)
        """
        # Risk score is inverted: 0 risk -> 100 pts; 100 risk -> 0 pts
        clamped_risk = max(Decimal("0.0000"), min(Decimal("100.0000"), composite_risk_score))
        risk_score = Decimal("100.0000") - clamped_risk

        # Penalty proportional to missing data / uncertainty (up to 15 points)
        penalty = (uncertainty_score * Decimal("15.0000")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        return risk_score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP), penalty

    @classmethod
    def normalize_terms(
        cls,
        payment_terms: str,
        warranty_months: int,
    ) -> Decimal:
        """Normalize commercial payment and warranty terms."""
        terms_upper = (payment_terms or "").upper().strip()

        # Deterministic payment terms lookup table
        terms_scores = {
            "NET 120": Decimal("100.0000"),
            "NET 90": Decimal("95.0000"),
            "NET 60": Decimal("85.0000"),
            "NET 45": Decimal("75.0000"),
            "NET 30": Decimal("65.0000"),
            "NET 15": Decimal("45.0000"),
            "NET 7": Decimal("25.0000"),
            "COD": Decimal("15.0000"),
            "ADVANCE": Decimal("5.0000"),
            "100% ADVANCE": Decimal("0.0000"),
        }

        base_terms_score = Decimal("60.0000")
        for key, val in terms_scores.items():
            if key in terms_upper:
                base_terms_score = val
                break

        # Warranty bonus: +2.5 pts for every 6 months above 12 months; -5 pts if under 12
        warranty_adjustment = Decimal("0.0000")
        if warranty_months > 12:
            extra_months = warranty_months - 12
            warranty_adjustment = (Decimal(str(extra_months)) / Decimal("6.0")) * Decimal("2.5000")
        elif warranty_months < 12:
            warranty_adjustment = Decimal("-5.0000")

        total = max(Decimal("0.0000"), min(Decimal("100.0000"), base_terms_score + warranty_adjustment))
        return total.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
