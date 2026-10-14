"""Stateless, deterministic Total Landed Cost calculation service."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple
from app.schemas.scoring import VendorQuotationInput

# Standard exchange rates relative to USD for deterministic currency normalization
DEFAULT_EXCHANGE_RATES: Dict[str, Decimal] = {
    "USD": Decimal("1.0000"),
    "EUR": Decimal("1.0850"),
    "GBP": Decimal("1.2950"),
    "CAD": Decimal("0.7300"),
    "JPY": Decimal("0.0065"),
    "INR": Decimal("0.0120"),
    "AUD": Decimal("0.6600"),
}


class LandedCostCalculator:
    """Calculates standardized Total Landed Cost with Incoterms and currency adjustments."""

    @classmethod
    def calculate(
        cls,
        quote: VendorQuotationInput,
        target_currency: str = "USD",
        exchange_rates: Dict[str, Decimal] = None,
    ) -> Tuple[Decimal, Dict[str, Decimal]]:
        """Calculate Total Landed Cost in target currency.
        
        Formula:
        Landed Cost = Base Price - Discount + Freight + Insurance + Tax
        (adjusted for Incoterms obligations)
        """
        rates = exchange_rates or DEFAULT_EXCHANGE_RATES
        currency = quote.currency.upper()
        if currency not in rates:
            raise ValueError(f"Unsupported quotation currency '{currency}'. No exchange rate defined.")
        
        target_curr = target_currency.upper()
        if target_curr not in rates:
            raise ValueError(f"Unsupported target currency '{target_curr}'.")

        # Convert to USD then to target currency
        rate_to_usd = rates[currency]
        usd_to_target = Decimal("1.0000") / rates[target_curr]
        conversion_factor = rate_to_usd * usd_to_target

        base_price_conv = (quote.base_price * conversion_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        discount_conv = (quote.discount_amount * conversion_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        freight_conv = (quote.freight_cost * conversion_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        insurance_conv = (quote.insurance_cost * conversion_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        tax_conv = (quote.tax_amount * conversion_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Incoterms adjustments: if vendor quoted EXW or FOB but omitted freight/insurance, apply standard estimates
        incoterms = (quote.incoterms or "DDP").upper().strip()
        incoterms_surcharge = Decimal("0.0000")

        if incoterms == "EXW" and freight_conv == Decimal("0.0000"):
            # Ex Works: buyer pays freight + insurance (estimate 5% freight, 1% insurance)
            incoterms_surcharge += (base_price_conv * Decimal("0.0600")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        elif incoterms == "FOB" and freight_conv == Decimal("0.0000"):
            # Free On Board: buyer pays international freight (estimate 3.5%)
            incoterms_surcharge += (base_price_conv * Decimal("0.0350")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        elif incoterms == "CIF" and insurance_conv == Decimal("0.0000"):
            # CIF includes freight and insurance to destination port; domestic carriage estimate 1.5%
            incoterms_surcharge += (base_price_conv * Decimal("0.0150")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        total_landed_cost = (
            base_price_conv
            - discount_conv
            + freight_conv
            + insurance_conv
            + tax_conv
            + incoterms_surcharge
        ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        breakdown = {
            "base_price_normalized": base_price_conv,
            "discount_normalized": discount_conv,
            "freight_normalized": freight_conv,
            "insurance_normalized": insurance_conv,
            "tax_normalized": tax_conv,
            "incoterms_surcharge": incoterms_surcharge,
            "incoterms": incoterms,
            "original_currency": currency,
            "target_currency": target_curr,
            "conversion_factor": conversion_factor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            "total_landed_cost": total_landed_cost,
        }

        return total_landed_cost, breakdown
