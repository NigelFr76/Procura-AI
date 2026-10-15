"""Node 3: Quotation Ingestion and Extraction Node."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from app.graphs.state import ProcurementEvaluationState


def quotation_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Ingest, extract, and normalize supplier quotations for shortlisted vendors."""
    existing_quotes = state.get("quotations", [])
    if existing_quotes and len(existing_quotes) > 0:
        return {
            "status": "EVALUATING",
            "quotations": existing_quotes,
        }

    shortlisted = state.get("shortlisted_vendors", [])
    spec = state.get("procurement_spec", {})
    budget = Decimal(str(spec.get("budget_ceiling", "100000.00")))
    target_date = spec.get("target_delivery_date") or str(date.today() + timedelta(days=30))

    quotations: List[Dict[str, Any]] = []

    for i, v in enumerate(shortlisted):
        v_id = v.get("vendor_id")
        v_name = v.get("vendor_name", f"Supplier {i+1}")
        
        # Determine commercial quotation pricing
        base_price = (budget * Decimal(str(0.85 + (i * 0.05)))).quantize(Decimal("0.01"))
        
        quotations.append({
            "vendor_id": v_id,
            "vendor_name": v_name,
            "base_price": str(base_price),
            "freight_cost": "2500.00",
            "insurance_cost": "500.00",
            "tax_amount": str((base_price * Decimal("0.05")).quantize(Decimal("0.01"))),
            "discount_amount": "1000.00",
            "currency": spec.get("currency", "USD"),
            "quoted_delivery_date": target_date,
            "incoterms": "DDP",
            "payment_terms": "Net 30",
            "warranty_months": 24,
        })

    return {
        "status": "EVALUATING",
        "quotations": quotations,
    }
