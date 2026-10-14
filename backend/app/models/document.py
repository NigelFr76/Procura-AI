"""Document management and object storage tracking."""

import enum
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest
    from app.models.vendor import Vendor
    from app.models.quotation import Quotation


class DocumentUploadStatus(str, enum.Enum):
    """File upload and processing lifecycle."""
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Document(Base, TimestampMixin, TenantMixin):
    """Quotation document, RFP specification, or supplier compliance certificate."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("procurement_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    upload_status: Mapped[DocumentUploadStatus] = mapped_column(
        Enum(DocumentUploadStatus, native_enum=False),
        default=DocumentUploadStatus.PENDING,
        nullable=False,
    )
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    request: Mapped[Optional["ProcurementRequest"]] = relationship(
        "ProcurementRequest",
        back_populates="documents",
    )
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")
    quotation: Mapped[Optional["Quotation"]] = relationship(
        "Quotation",
        back_populates="document",
        uselist=False,
    )
