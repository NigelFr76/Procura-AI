"""Schemas for document parsing, layout coordinates, and evidence provenance."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedTextBlock(BaseModel):
    """Text snippet extracted with normalized coordinate bounding box."""
    text: str
    page_number: int = Field(..., ge=1)
    # Normalized coordinates [x1, y1, x2, y2] between 0.0 and 1.0 relative to page dimensions
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    font_size: Optional[float] = None
    is_suspicious_hidden: bool = False


class ParsedTable(BaseModel):
    """Structured table extracted from quotation or specification."""
    page_number: int = Field(..., ge=1)
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)


class ParsedDocumentResult(BaseModel):
    """Structured extraction result preserving layout coordinates and provenance."""
    document_id: uuid.UUID
    file_name: str
    total_pages: int
    text_blocks: List[ParsedTextBlock] = Field(default_factory=list)
    tables: List[ParsedTable] = Field(default_factory=list)
    full_text: str
    sha256_hash: str
    has_injection_risk: bool = False
    security_warnings: List[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    """Chunk of document text prepared for hybrid search with provenance citations."""
    chunk_id: str
    document_id: uuid.UUID
    page_number: int
    bbox: List[float]
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
