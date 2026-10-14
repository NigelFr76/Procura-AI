"""Agent 3: Quotation Analysis Agent with evidence coordinate linking and prompt sanitization."""

import re
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_provider import llm_provider
from app.agents.prompts.quotation_prompts import QUOTATION_ANALYSIS_SYSTEM_PROMPT
from app.schemas.document import ParsedDocumentResult
from app.schemas.quotation_extraction import (
    EvidenceLocation,
    ExtractedQuotationItem,
    NormalizedQuotationResult,
)


class QuotationAnalysisAgent:
    """Specialized agent extracting structured commercial terms with bounding box evidence citations."""

    @classmethod
    def analyze_quotation(
        cls,
        parsed_doc: ParsedDocumentResult,
        vendor_id: uuid.UUID,
        vendor_name: str,
    ) -> NormalizedQuotationResult:
        """Extract prices, line items, delivery commitments, and terms, preserving visual coordinates."""
        # Sanitize text and wrap in untrusted container
        sanitized_full_text = parsed_doc.full_text.replace("<", "&lt;").replace(">", "&gt;")

        messages = [
            SystemMessage(content=QUOTATION_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Document ID: {parsed_doc.document_id}\n"
                    f"Vendor: {vendor_name} (ID: {vendor_id})\n"
                    f"File Name: {parsed_doc.file_name}\n"
                    f"Total Pages: {parsed_doc.total_pages}\n\n"
                    f"<untrusted_quotation_text>\n{sanitized_full_text}\n</untrusted_quotation_text>\n"
                )
            ),
        ]

        def fallback_parser() -> NormalizedQuotationResult:
            """Deterministic layout and keyword extractor when LLM key is absent."""
            text = parsed_doc.full_text
            ambiguity_flags: List[str] = []
            evidence_map: Dict[str, EvidenceLocation] = {}

            # Helper to find matching block for text
            def find_block(pattern: str) -> Optional[EvidenceLocation]:
                for b in parsed_doc.text_blocks:
                    if re.search(pattern, b.text, re.IGNORECASE):
                        return EvidenceLocation(
                            document_id=parsed_doc.document_id,
                            page_number=b.page_number,
                            bbox=b.bbox,
                            text_snippet=b.text[:120],
                        )
                # Fallback to first block
                if parsed_doc.text_blocks:
                    fb = parsed_doc.text_blocks[0]
                    return EvidenceLocation(
                        document_id=parsed_doc.document_id,
                        page_number=fb.page_number,
                        bbox=fb.bbox,
                        text_snippet=fb.text[:120],
                    )
                return None

            # Detect Grand Total
            total_amount = None
            grand_total_match = re.search(r"(?:Grand Total|Total Amount|Total Price|Total)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
            if grand_total_match:
                try:
                    total_amount = Decimal(grand_total_match.group(1).replace(",", ""))
                except Exception:
                    pass

            # Detect Base Price / Subtotal
            base_price = None
            base_price_match = re.search(r"(?:Base Price|Subtotal|Item Total)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
            if base_price_match:
                try:
                    base_price = Decimal(base_price_match.group(1).replace(",", ""))
                except Exception:
                    pass

            # Detect Freight
            freight = Decimal("0.00")
            freight_match = re.search(r"(?:Freight|Shipping)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
            if freight_match:
                try:
                    freight = Decimal(freight_match.group(1).replace(",", ""))
                except Exception:
                    pass

            # Detect Tax
            tax = Decimal("0.00")
            tax_match = re.search(r"(?:Tax|VAT|GST)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
            if tax_match:
                try:
                    tax = Decimal(tax_match.group(1).replace(",", ""))
                except Exception:
                    pass

            # Detect Discount
            discount = Decimal("0.00")
            discount_match = re.search(r"(?:Discount|Rebate)[:\s]*\$?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
            if discount_match:
                try:
                    discount = Decimal(discount_match.group(1).replace(",", ""))
                except Exception:
                    pass

            # Reconcile Base Price and Total
            if total_amount is not None and base_price is not None:
                pass
            elif total_amount is not None:
                base_price = max(Decimal("0.00"), total_amount - freight - tax + discount)
            elif base_price is not None:
                total_amount = base_price + freight + tax - discount
            else:
                base_price = Decimal("10000.00")
                total_amount = Decimal("10000.00")

            # Detect delivery date
            delivery_date = date.today() + timedelta(days=30)
            date_match = re.search(r"(?:Delivery|Date|Valid)[:\s]*\b(202\d-[01]\d-[0-3]\d)\b", text, re.IGNORECASE)
            if date_match:
                try:
                    delivery_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
                except Exception:
                    pass
            else:
                ambiguity_flags.append("Quoted delivery date was not explicitly stated; default 30 days applied.")

            # Detect Incoterms
            incoterms = "DDP"
            for term in ["EXW", "FOB", "CIF", "DDP", "DAP", "CIP"]:
                if re.search(rf"\b{term}\b", text):
                    incoterms = term
                    break
            else:
                ambiguity_flags.append("Incoterms not explicitly specified in document; defaulted to DDP.")

            # Detect Payment Terms
            payment_terms = "Net 30"
            for pt in ["Net 60", "Net 45", "Net 30", "Net 15", "100% Advance", "COD"]:
                if re.search(rf"\b{pt}\b", text, re.IGNORECASE):
                    payment_terms = pt
                    break
            else:
                ambiguity_flags.append("Payment terms not explicitly defined; defaulted to Net 30.")

            # Currency
            currency = "USD"
            if "EUR" in text or "€" in text:
                currency = "EUR"
            elif "GBP" in text or "£" in text:
                currency = "GBP"

            # Locate evidence
            ev_price = find_block(r"Total|Price|Amount|\$")
            if ev_price:
                evidence_map["base_price"] = ev_price
                evidence_map["total_quote_amount"] = ev_price

            ev_del = find_block(r"Delivery|Date|202")
            if ev_del:
                evidence_map["quoted_delivery_date"] = ev_del

            ev_terms = find_block(r"Net|Payment|Terms")
            if ev_terms:
                evidence_map["payment_terms"] = ev_terms

            # Extract line items from parsed tables or heuristic
            line_items: List[ExtractedQuotationItem] = []
            if parsed_doc.tables and len(parsed_doc.tables[0].rows) > 0:
                table = parsed_doc.tables[0]
                for r_idx, row in enumerate(table.rows):
                    if len(row) >= 2:
                        line_items.append(
                            ExtractedQuotationItem(
                                description=row[0] or f"Item #{r_idx+1}",
                                quantity=Decimal("1.00"),
                                unit_price=base_price,
                                total_price=base_price,
                                evidence=EvidenceLocation(
                                    document_id=parsed_doc.document_id,
                                    page_number=table.page_number,
                                    bbox=table.bbox,
                                    text_snippet=" | ".join(row),
                                ),
                            )
                        )
            else:
                line_items.append(
                    ExtractedQuotationItem(
                        description="Extracted Quotation Package",
                        quantity=Decimal("1.00"),
                        unit_price=base_price,
                        total_price=base_price,
                        evidence=ev_price,
                    )
                )

            return NormalizedQuotationResult(
                document_id=parsed_doc.document_id,
                vendor_name=vendor_name,
                quote_reference=parsed_doc.file_name.replace(".pdf", ""),
                currency=currency,
                base_price=base_price,
                freight_cost=freight,
                tax_amount=tax,
                discount_amount=discount,
                total_quote_amount=total_amount,
                quoted_delivery_date=delivery_date,
                incoterms=incoterms,
                payment_terms=payment_terms,
                warranty_months=12,
                line_items=line_items,
                ambiguity_flags=ambiguity_flags,
                evidence_locations=evidence_map,
            )

        return llm_provider.generate_structured(
            messages=messages,
            response_model=NormalizedQuotationResult,
            fallback_factory=fallback_parser,
        )
