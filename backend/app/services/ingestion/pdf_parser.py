"""Layout-aware PDF parsing service with coordinate tracking and prompt injection defense."""

import hashlib
import re
import uuid
from typing import List, Tuple
import fitz # PyMuPDF

from app.schemas.document import (
    ParsedDocumentResult,
    ParsedTextBlock,
    ParsedTable,
)

# Known prompt injection signatures to detect in untrusted supplier documents
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?rules",
    r"override\s+scoring",
    r"assign\s+(this\s+vendor|me)\s+(a\s+)?score\s+of\s+100",
    r"<script.*?>",
]


class PDFParser:
    """Extracts text blocks and tables from PDFs with normalized coordinates and security checks."""

    @classmethod
    def parse_bytes(
        cls,
        pdf_bytes: bytes,
        document_id: uuid.UUID,
        file_name: str,
    ) -> ParsedDocumentResult:
        """Parse PDF byte stream into structured text blocks with normalized coordinates."""
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        text_blocks: List[ParsedTextBlock] = []
        tables: List[ParsedTable] = []
        full_text_parts: List[str] = []
        security_warnings: List[str] = []
        has_injection_risk = False

        try:
            for page_idx, page in enumerate(doc, start=1):
                rect = page.rect
                width = rect.width or 1.0
                height = rect.height or 1.0

                # 1. Extract visual blocks with bounding boxes
                blocks = page.get_text("blocks")
                for b in blocks:
                    # b: (x0, y0, x1, y1, text, block_no, block_type)
                    if len(b) >= 5:
                        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
                        clean_text = text.strip()
                        if not clean_text:
                            continue

                        # Normalize coordinates to percentage of page width/height [0.0 - 1.0]
                        norm_bbox = [
                            round(max(0.0, min(1.0, x0 / width)), 4),
                            round(max(0.0, min(1.0, y0 / height)), 4),
                            round(max(0.0, min(1.0, x1 / width)), 4),
                            round(max(0.0, min(1.0, y1 / height)), 4),
                        ]

                        # Check for injection patterns
                        for pattern in INJECTION_PATTERNS:
                            if re.search(pattern, clean_text, re.IGNORECASE):
                                has_injection_risk = True
                                security_warnings.append(
                                    f"Page {page_idx}: Detected suspicious prompt pattern '{pattern}' in text snippet."
                                )

                        text_blocks.append(
                            ParsedTextBlock(
                                text=clean_text,
                                page_number=page_idx,
                                bbox=norm_bbox,
                            )
                        )
                        full_text_parts.append(f"[Page {page_idx}] {clean_text}")

                # 2. Check for micro-font / invisible hidden text injection
                page_dict = page.get_text("dict")
                for block in page_dict.get("blocks", []):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            span_text = span.get("text", "").strip()
                            span_size = span.get("size", 10.0)
                            if span_text and span_size < 2.5:
                                has_injection_risk = True
                                security_warnings.append(
                                    f"Page {page_idx}: Detected hidden micro-font text (size {span_size:.1f}pt): '{span_text[:50]}'"
                                )

                # 3. Extract tables using PyMuPDF table finder
                try:
                    tabs = page.find_tables()
                    for tab in tabs:
                        tab_rect = tab.bbox
                        norm_tab_bbox = [
                            round(max(0.0, min(1.0, tab_rect[0] / width)), 4),
                            round(max(0.0, min(1.0, tab_rect[1] / height)), 4),
                            round(max(0.0, min(1.0, tab_rect[2] / width)), 4),
                            round(max(0.0, min(1.0, tab_rect[3] / height)), 4),
                        ]
                        df = tab.extract()
                        if df and len(df) > 0:
                            headers = [str(col).strip() if col is not None else "" for col in df[0]]
                            rows = [
                                [str(cell).strip() if cell is not None else "" for cell in row]
                                for row in df[1:]
                            ]
                            tables.append(
                                ParsedTable(
                                    page_number=page_idx,
                                    bbox=norm_tab_bbox,
                                    headers=headers,
                                    rows=rows,
                                )
                            )
                except Exception:
                    # Table extraction optional fallback
                    pass
        finally:
            doc.close()

        return ParsedDocumentResult(
            document_id=document_id,
            file_name=file_name,
            total_pages=total_pages,
            text_blocks=text_blocks,
            tables=tables,
            full_text="\n\n".join(full_text_parts),
            sha256_hash=sha256,
            has_injection_risk=has_injection_risk,
            security_warnings=security_warnings,
        )
