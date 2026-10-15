"""Schemas for Agent 6: Negotiation Simulation Agent."""

import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class NegotiationSimInput(BaseModel):
    """Parameters passed to Agent 6 to simulate supplier counteroffers within policy boundaries."""
    vendor_id: uuid.UUID
    vendor_name: str
    quoted_base_price: Decimal = Field(..., gt=0)
    quoted_delivery_days: int = Field(default=30, ge=1)
    quoted_payment_terms: str = Field(default="Net 30")
    quoted_warranty_months: int = Field(default=12, ge=0)
    
    # Negotiation Targets
    target_price_discount_pct: Decimal = Field(default=Decimal("10.00"), ge=0, le=50)
    target_payment_terms: Optional[str] = "Net 60"
    target_delivery_days: Optional[int] = None
    target_warranty_months: Optional[int] = None
    
    # Behavioral boundaries
    vendor_elasticity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    cost_floor_pct: Decimal = Field(
        default=Decimal("82.00"),
        ge=50,
        le=95,
        description="Minimum pricing threshold below which the vendor strictly refuses to concede",
    )


class NegotiationRound(BaseModel):
    """Simulated exchange round between enterprise buyer and vendor."""
    round_number: int
    buyer_offer_price: Decimal
    vendor_counter_price: Decimal
    vendor_concessions: List[str] = Field(default_factory=list)
    vendor_withheld: List[str] = Field(default_factory=list)
    concession_rationale: str


class NegotiationSimResult(BaseModel):
    """Comprehensive multi-round hypothetical negotiation simulation outcome."""
    vendor_id: uuid.UUID
    vendor_name: str
    rounds: List[NegotiationRound] = Field(default_factory=list)
    recommended_opening_price: Decimal
    walkaway_price: Decimal
    expected_final_price: Decimal
    projected_savings_amount: Decimal
    projected_savings_pct: Decimal
    negotiation_leverage: str = "MODERATE"
    tactical_recommendations: List[str] = Field(default_factory=list)
    risk_assessment: str
    is_hypothetical_simulation: bool = True
