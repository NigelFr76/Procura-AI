"""Unit tests for Agent 3: Quotation Analysis Agent."""

import uuid
from decimal import Decimal
import fitz # PyMuPDF

from app.agents.quotation_agent import QuotationAnalysisAgent
from app.services.ingestion.pdf_parser import PDFParser


def create_sample_quotation_pdf(lines: list) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    y = 60
    for line in lines:
        page.insert_text((50, y), line, fontsize=11)
        y += 30
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_quotation_analysis_agent_extraction():
    """Verify commercial terms extraction and bounding box coordinate linking."""
    lines = [
        "OFFICIAL QUOTATION: Precision Alloys Gmbh",
        "Quote Reference: QT-2026-991",
        "Currency: USD",
        "Base Price: $420,000.00",
        "Freight Shipping: $12,500.00",
        "Grand Total Amount: $432,500.00",
        "Delivery Date: 2026-10-25",
        "Incoterms: DDP",
        "Payment Terms: Net 60",
        "Warranty Period: 24 Months",
    ]
    pdf_bytes = create_sample_quotation_pdf(lines)
    doc_id = uuid.uuid4()
    v_id = uuid.uuid4()

    parsed_doc = PDFParser.parse_bytes(pdf_bytes, doc_id, "quote_precision.pdf")
    quote_result = QuotationAnalysisAgent.analyze_quotation(parsed_doc, v_id, "Precision Alloys Gmbh")

    assert quote_result.document_id == doc_id
    assert quote_result.vendor_name == "Precision Alloys Gmbh"
    assert quote_result.total_quote_amount == Decimal("432500.00")
    assert quote_result.freight_cost == Decimal("12500.00")
    assert quote_result.base_price == Decimal("420000.00")
    assert quote_result.incoterms == "DDP"
    assert quote_result.payment_terms == "Net 60"
    assert str(quote_result.quoted_delivery_date) == "2026-10-25"

    # Evidence citations should exist and contain bounding box
    assert len(quote_result.evidence_locations) > 0
    assert "total_quote_amount" in quote_result.evidence_locations
    ev = quote_result.evidence_locations["total_quote_amount"]
    assert ev.document_id == doc_id
    assert ev.page_number == 1
    assert len(ev.bbox) == 4
