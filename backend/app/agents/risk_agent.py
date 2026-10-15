"""Agent 5: Risk Assessment Agent for supplier telemetry and qualitative risk synthesis."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.risk_prompts import RISK_ASSESSMENT_SYSTEM_PROMPT
from app.models.risk import RiskTier
from app.schemas.risk import (
    RiskAssessmentResult,
    RiskFactorDetail,
    RiskInput,
)


class RiskAssessmentAgent:
    """Specialized agent that evaluates vendor operational, financial, and supply chain risks."""

    @classmethod
    def assess(cls, input_data: RiskInput) -> RiskAssessmentResult:
        """Calculate multi-dimensional risk metrics and synthesize mitigations."""
        # 1. Delivery Risk [0 - 100]
        if input_data.historical_orders_count == 0:
            delivery_risk = Decimal("35.00")
        else:
            otd = max(Decimal("0.00"), min(Decimal("1.00"), input_data.on_time_delivery_rate))
            delivery_risk = ((Decimal("1.00") - otd) * Decimal("100.00")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # 2. Quality Risk [0 - 100]
        if input_data.historical_orders_count == 0:
            quality_risk = Decimal("30.00")
        else:
            defect = max(Decimal("0.00"), min(Decimal("1.00"), input_data.defect_rate))
            # 2% defect rate maps to 20/100 risk, 5% to 50/100, 10%+ to 100/100
            quality_risk = min(Decimal("100.00"), defect * Decimal("1000.00")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # 3. Concentration Risk [0 - 100]
        conc_pct = max(Decimal("0.00"), min(Decimal("100.00"), input_data.spend_concentration_pct))
        concentration_risk = min(Decimal("100.00"), conc_pct * Decimal("1.20")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 4. Geopolitical & Sanctions Risk [0 - 100]
        if input_data.sanction_flag:
            geopolitical_risk = Decimal("100.00")
        else:
            country = (input_data.country or "USA").upper()
            high_risk_countries = {"RUSSIA", "IRAN", "NORTH KOREA", "SYRIA", "CUBA", "BELARUS"}
            elevated_risk_countries = {"VENEZUELA", "MYANMAR", "YEMEN", "SUDAN"}
            
            if country in high_risk_countries:
                geopolitical_risk = Decimal("95.00")
            elif country in elevated_risk_countries:
                geopolitical_risk = Decimal("60.00")
            else:
                geopolitical_risk = Decimal("10.00")

        # 5. Financial Risk [0 - 100]
        financial_risk = Decimal("15.00")
        notes = (input_data.qualitative_notes or "").lower()
        if any(w in notes for w in ["bankruptcy", "insolvent", "insolvency", "liquidation", "restructuring"]):
            financial_risk = Decimal("90.00")
        elif any(w in notes for w in ["downgrade", "cashflow", "debt", "lawsuit", "delayed payment"]):
            financial_risk = Decimal("65.00")

        # 6. Uncertainty Penalty (Sparse Data Penalty) [0 - 1]
        if input_data.historical_orders_count == 0:
            uncertainty_score = Decimal("0.5000")
        elif input_data.historical_orders_count < 5:
            uncertainty_score = (
                Decimal(5 - input_data.historical_orders_count) * Decimal("0.1000")
            ).quantize(Decimal("0.0001"))
        else:
            uncertainty_score = Decimal("0.0000")

        # 7. Composite Risk Score [0 - 100]
        # Weights: Delivery 30%, Quality 30%, Financial 15%, Concentration 15%, Geopolitical 10%
        base_composite = (
            (delivery_risk * Decimal("0.30"))
            + (quality_risk * Decimal("0.30"))
            + (financial_risk * Decimal("0.15"))
            + (concentration_risk * Decimal("0.15"))
            + (geopolitical_risk * Decimal("0.10"))
        )
        
        # Uncertainty elevates composite risk slightly when unproven
        composite_risk_score = min(
            Decimal("100.00"),
            base_composite + (uncertainty_score * Decimal("15.00")),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 8. Risk Tier
        if input_data.sanction_flag or composite_risk_score > Decimal("75.00"):
            risk_tier = RiskTier.CRITICAL
        elif composite_risk_score > Decimal("50.00"):
            risk_tier = RiskTier.HIGH
        elif composite_risk_score > Decimal("25.00"):
            risk_tier = RiskTier.MEDIUM
        else:
            risk_tier = RiskTier.LOW

        # 9. Factor Telemetry & Mitigations
        factors: List[RiskFactorDetail] = []
        mitigations: List[str] = []

        if delivery_risk > Decimal("30.00"):
            factors.append(
                RiskFactorDetail(
                    category="DELIVERY",
                    severity=RiskTier.HIGH if delivery_risk > 50 else RiskTier.MEDIUM,
                    score=float(delivery_risk),
                    description=f"Delivery risk elevated ({delivery_risk}/100) based on historical delivery performance.",
                    mitigation_suggestion="Include liquidated damages clause of 1% per day of delivery delay.",
                )
            )
            mitigations.append("Mandate 10% milestone retention until final on-site acceptance testing.")

        if quality_risk > Decimal("25.00"):
            factors.append(
                RiskFactorDetail(
                    category="QUALITY",
                    severity=RiskTier.HIGH if quality_risk > 50 else RiskTier.MEDIUM,
                    score=float(quality_risk),
                    description=f"Quality defect risk elevated ({quality_risk}/100) based on return rates.",
                    mitigation_suggestion="Require pre-shipment third-party inspection (TPI) and Certificate of Conformance.",
                )
            )
            mitigations.append("Incorporate 24-month extended warranty with rapid replacement SLA.")

        if concentration_risk > Decimal("40.00"):
            factors.append(
                RiskFactorDetail(
                    category="CONCENTRATION",
                    severity=RiskTier.HIGH if concentration_risk > 70 else RiskTier.MEDIUM,
                    score=float(concentration_risk),
                    description=f"High single-source spend concentration ({concentration_risk}/100).",
                    mitigation_suggestion="Establish secondary supplier contract for at least 30% split allocation.",
                )
            )
            mitigations.append("Dual-source critical subcomponents to avoid operational deadlock.")

        if financial_risk > Decimal("50.00"):
            factors.append(
                RiskFactorDetail(
                    category="FINANCIAL",
                    severity=RiskTier.CRITICAL if financial_risk > 75 else RiskTier.HIGH,
                    score=float(financial_risk),
                    description=f"Financial health indicators flag potential supplier distress ({financial_risk}/100).",
                    mitigation_suggestion="Require parent company financial guarantee or irrevocable letter of credit.",
                )
            )
            mitigations.append("Structure payments strictly upon verified delivery; avoid advance deposits.")

        if geopolitical_risk > Decimal("50.00"):
            factors.append(
                RiskFactorDetail(
                    category="GEOPOLITICAL",
                    severity=RiskTier.CRITICAL if geopolitical_risk > 75 else RiskTier.HIGH,
                    score=float(geopolitical_risk),
                    description=f"Supplier jurisdiction poses high geopolitical or regulatory risk ({geopolitical_risk}/100).",
                    mitigation_suggestion="Ensure alternate domestic/allied warehousing or stock reserve.",
                )
            )
            mitigations.append("Verify compliance with export control licenses and trade sanctions.")

        if uncertainty_score > Decimal("0.0000"):
            factors.append(
                RiskFactorDetail(
                    category="DELIVERY",
                    severity=RiskTier.MEDIUM,
                    score=float(uncertainty_score * 100),
                    description=f"Sparse historical order track record ({input_data.historical_orders_count} previous orders).",
                    mitigation_suggestion="Require initial low-volume pilot batch before full contract commitment.",
                )
            )
            mitigations.append("Establish weekly milestone check-ins during early production phases.")

        if not mitigations:
            mitigations.append("Maintain standard vendor performance monitoring and quarterly review.")

        return RiskAssessmentResult(
            vendor_id=input_data.vendor_id,
            composite_risk_score=composite_risk_score,
            risk_tier=risk_tier,
            delivery_risk=delivery_risk,
            quality_risk=quality_risk,
            financial_risk=financial_risk,
            concentration_risk=concentration_risk,
            geopolitical_risk=geopolitical_risk,
            uncertainty_score=uncertainty_score,
            factors=factors,
            mitigations=mitigations,
        )
