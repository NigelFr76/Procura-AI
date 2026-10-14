"""SQLAlchemy declarative models registry."""

from app.models.base import Base, GUID, TimestampMixin, TenantMixin, VectorType
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.vendor import Vendor, VendorStatus
from app.models.vendor_performance import VendorPerformanceHistory
from app.models.procurement_request import (
    ProcurementRequest,
    ProcurementRequestItem,
    RequestStatus,
    RequestPriority,
)
from app.models.document import Document, DocumentUploadStatus
from app.models.quotation import Quotation, QuotationLineItem
from app.models.compliance import (
    ComplianceRule,
    ComplianceRuleType,
    ComplianceStatus,
    ComplianceCheck,
)
from app.models.risk import RiskAssessment, RiskTier
from app.models.scoring_policy import ScoringPolicy
from app.models.evaluation import Evaluation, EvaluationStatus, VendorScore
from app.models.scenario import ScenarioEvaluation, ScenarioStatus
from app.models.approval import ApprovalRecord, ApprovalAction
from app.models.audit import AuditEvent, AuditAction

__all__ = [
    "Base",
    "GUID",
    "TimestampMixin",
    "TenantMixin",
    "VectorType",
    "Organization",
    "User",
    "UserRole",
    "Vendor",
    "VendorStatus",
    "VendorPerformanceHistory",
    "ProcurementRequest",
    "ProcurementRequestItem",
    "RequestStatus",
    "RequestPriority",
    "Document",
    "DocumentUploadStatus",
    "Quotation",
    "QuotationLineItem",
    "ComplianceRule",
    "ComplianceRuleType",
    "ComplianceStatus",
    "ComplianceCheck",
    "RiskAssessment",
    "RiskTier",
    "ScoringPolicy",
    "Evaluation",
    "EvaluationStatus",
    "VendorScore",
    "ScenarioEvaluation",
    "ScenarioStatus",
    "ApprovalRecord",
    "ApprovalAction",
    "AuditEvent",
    "AuditAction",
]
