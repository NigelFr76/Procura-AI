"""FastAPI router for quotation document uploads and OCR coordinate extraction."""

import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_tenant_id
from app.services.ingestion.pdf_parser import PDFParser

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_quotation_document(
    file: UploadFile = File(...),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Upload supplier quotation PDF, execute coordinate OCR extraction, and scan for prompt injections."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF quotation files are supported for coordinate layout extraction.",
        )

    file_bytes = await file.read()
    doc_id = uuid.uuid4()

    parsed = PDFParser.parse_bytes(
        pdf_bytes=file_bytes,
        document_id=doc_id,
        file_name=file.filename,
    )

    from app.services.audit.audit_service import AuditAction, AuditService
    audit_action = (
        AuditAction.PROMPT_INJECTION_FLAGGED
        if parsed.has_injection_risk
        else AuditAction.DOCUMENT_INGESTED
    )
    AuditService.record_event(
        tenant_id=str(tenant_id),
        user_id="supplier-uploader",
        action=audit_action,
        payload={
            "document_id": str(doc_id),
            "file_name": file.filename,
            "sha256": parsed.sha256,
            "has_injection_risk": parsed.has_injection_risk,
            "security_warnings": parsed.security_warnings,
        },
    )

    return {
        "document_id": doc_id,
        "file_name": file.filename,
        "total_pages": parsed.total_pages,
        "sha256": parsed.sha256,
        "has_injection_risk": parsed.has_injection_risk,
        "security_warnings": parsed.security_warnings,
        "blocks_count": len(parsed.text_blocks),
        "tables_count": len(parsed.tables),
    }
