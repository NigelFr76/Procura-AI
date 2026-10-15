"""Multi-Agent intelligence package."""

from app.agents.llm_provider import LLMProvider, llm_provider
from app.agents.requirement_agent import RequirementAnalysisAgent
from app.agents.vendor_discovery_agent import VendorDiscoveryAgent
from app.agents.quotation_agent import QuotationAnalysisAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.explanation_agent import DecisionExplanationAgent


def __getattr__(name: str):
    if name in ("DecisionCoordinator", "coordinator"):
        from app.agents import coordinator_agent
        return getattr(coordinator_agent, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "LLMProvider",
    "llm_provider",
    "RequirementAnalysisAgent",
    "VendorDiscoveryAgent",
    "QuotationAnalysisAgent",
    "ComplianceAgent",
    "RiskAssessmentAgent",
    "DecisionExplanationAgent",
    "DecisionCoordinator",
    "coordinator",
]
