"""Agent 1: Requirement Analysis Agent for natural language procurement intake."""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.requirement_prompts import REQUIREMENT_ANALYSIS_SYSTEM_PROMPT
from app.schemas.spec import (
    RawProcurementInput,
    ExtractedItemSpec,
    ProcurementSpecification,
    ProcurementSpecResult,
)


class RequirementAnalysisAgent:
    """Specialized agent that parses natural language procurement requests into validated specifications."""

    @classmethod
    def analyze(cls, input_data: RawProcurementInput) -> ProcurementSpecResult:
        """Parse raw text, extract line items, budget, deadlines, and identify missing constraints."""
        messages = [
            SystemMessage(content=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Procurement Request:\n"
                    f"Description: {input_data.text}\n"
                    f"Budget Hint: {input_data.budget_ceiling}\n"
                    f"Target Date Hint: {input_data.target_delivery_date}\n"
                    f"Currency: {input_data.currency}\n"
                    f"Required Certifications: {input_data.required_certifications}\n"
                )
            ),
        ]

        def fallback_parser() -> ProcurementSpecResult:
            """Deterministic heuristic fallback when no external LLM key is configured."""
            text = input_data.text
            title = text.split(".")[0][:80] if "." in text else text[:80]
            
            # Detect budget
            budget = input_data.budget_ceiling
            if budget is None:
                budget_match = re.search(r"\$?\s*([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars|budget)?", text, re.IGNORECASE)
                if budget_match:
                    try:
                        clean_num = budget_match.group(1).replace(",", "")
                        budget = Decimal(clean_num)
                    except Exception:
                        budget = None

            # Detect delivery date
            delivery_date = input_data.target_delivery_date
            if delivery_date is None:
                date_match = re.search(r"\b(202\d-[01]\d-[0-3]\d)\b", text)
                if date_match:
                    try:
                        delivery_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
                    except Exception:
                        delivery_date = None

            # Detect line items and quantities
            items: List[ExtractedItemSpec] = []
            qty_match = re.search(r"(\d+)\s*(?:units|pieces|casings|sensors|kg|items)?\s*(?:of)?\s*([a-zA-Z0-9\s-]+)", text, re.IGNORECASE)
            if qty_match:
                qty = Decimal(qty_match.group(1))
                item_desc = qty_match.group(2).strip()
                items.append(
                    ExtractedItemSpec(
                        description=item_desc or "Procurement Item",
                        quantity=qty,
                        unit_of_measure="units",
                    )
                )

            # Check missing fields
            missing: List[str] = []
            clarifications: List[str] = []

            if not items:
                missing.append("line_items_quantity")
                clarifications.append("Please specify the exact items and numeric quantities required.")
            if budget is None:
                missing.append("budget_ceiling")
                clarifications.append("What is the approved budget ceiling for this procurement request?")
            if delivery_date is None:
                missing.append("target_delivery_date")
                clarifications.append("What is the required target delivery date (YYYY-MM-DD)?")

            is_complete = len(missing) == 0

            spec = ProcurementSpecification(
                title=title or "Procurement Project",
                description=text,
                items=items,
                budget_ceiling=budget,
                currency=input_data.currency or "USD",
                target_delivery_date=delivery_date,
                required_certifications=input_data.required_certifications or [],
            )

            return ProcurementSpecResult(
                spec=spec,
                is_complete=is_complete,
                missing_fields=missing,
                clarification_questions=clarifications,
                confidence_score=0.95 if is_complete else 0.5,
            )

        return llm_provider.generate_structured(
            messages=messages,
            response_model=ProcurementSpecResult,
            fallback_factory=fallback_parser,
        )
