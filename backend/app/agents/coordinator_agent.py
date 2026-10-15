"""Agent 9: Decision Coordinator for multi-agent orchestration and lifecycle management."""

import uuid
from typing import Any, Dict, List, Optional

from app.graphs.procurement_graph import (
    build_procurement_graph,
    execute_evaluation,
    resume_evaluation,
)
from app.graphs.state import ProcurementEvaluationState


class DecisionCoordinator:
    """Specialized controller managing LangGraph state flow, parallel evaluations, and human gates."""

    def __init__(self, checkpointer=None):
        self.graph = build_procurement_graph(checkpointer=checkpointer)

    def start_evaluation(
        self,
        raw_text: str,
        organization_id: str,
        budget_ceiling: Optional[float] = None,
        target_delivery_date: Optional[str] = None,
        currency: str = "USD",
        required_certifications: Optional[List[str]] = None,
        scoring_policy: Optional[Dict[str, Any]] = None,
        candidate_vendors: Optional[List[Dict[str, Any]]] = None,
        compliance_rules: Optional[List[Dict[str, Any]]] = None,
        quotations: Optional[List[Dict[str, Any]]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initialize and trigger the end-to-end multi-agent evaluation pipeline."""
        req_id = str(uuid.uuid4())
        eval_id = str(uuid.uuid4())
        t_id = thread_id or f"procure-eval-{eval_id}"

        initial_state: ProcurementEvaluationState = {
            "organization_id": organization_id,
            "request_id": req_id,
            "evaluation_id": eval_id,
            "thread_id": t_id,
            "status": "INTAKE",
            "is_clarification_needed": False,
            "clarification_questions": [],
            "missing_fields": [],
            "raw_input": {
                "text": raw_text,
                "budget_ceiling": budget_ceiling,
                "target_delivery_date": target_delivery_date,
                "currency": currency,
                "required_certifications": required_certifications or [],
                "candidate_vendors": candidate_vendors or [],
            },
            "scoring_policy": scoring_policy or {},
            "compliance_rules": compliance_rules or [],
            "quotations": quotations or [],
        }

        from app.services.audit.audit_service import AuditAction, AuditService
        AuditService.record_event(
            tenant_id=organization_id,
            user_id="system-coordinator",
            action=AuditAction.EVALUATION_STARTED,
            payload={
                "evaluation_id": eval_id,
                "thread_id": t_id,
                "budget_ceiling": budget_ceiling,
                "currency": currency,
            },
        )

        result = execute_evaluation(
            initial_state=initial_state,
            thread_id=t_id,
            graph=self.graph,
        )

        if result.get("scorecard"):
            sc = result["scorecard"]
            scores_list = sc.get("scores") or sc.get("ranking", [])
            winner_name = sc.get("recommended_vendor_name") or (scores_list[0].get("vendor_name") if scores_list else None)
            fingerprint = sc.get("input_hash") or sc.get("scoring_fingerprint")
            AuditService.record_event(
                tenant_id=organization_id,
                user_id="scoring-engine",
                action=AuditAction.EVALUATION_SCORED,
                payload={
                    "evaluation_id": eval_id,
                    "scoring_fingerprint": fingerprint,
                    "winner": winner_name,
                },
            )

        return result

    def submit_human_approval(
        self,
        thread_id: str,
        action: str,  # "APPROVED", "REJECTED", "MODIFICATION_REQUESTED"
        comments: str,
        approver_user_id: str,
    ) -> Dict[str, Any]:
        """Resume an interrupted evaluation with authorized human sign-off."""
        approval_payload = {
            "action": action,
            "comments": comments,
            "approver_user_id": approver_user_id,
        }
        resumed = resume_evaluation(
            thread_id=thread_id,
            approval_data=approval_payload,
            graph=self.graph,
        )

        from app.services.audit.audit_service import AuditAction, AuditService
        audit_action = (
            AuditAction.HITL_APPROVAL_GRANTED
            if action.upper() == "APPROVED"
            else AuditAction.HITL_REJECTION_ISSUED
        )
        AuditService.record_event(
            tenant_id=resumed.get("organization_id", "00000000-0000-0000-0000-000000000001"),
            user_id=approver_user_id,
            action=audit_action,
            payload={
                "thread_id": thread_id,
                "action": action,
                "comments": comments,
                "signature_hash": resumed.get("signature_hash"),
            },
        )

        return resumed

    def get_evaluation_state(self, thread_id: str) -> Dict[str, Any]:
        """Fetch current checkpointed state snapshot for a running or interrupted evaluation thread."""
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = self.graph.get_state(config)
        return state_snapshot.values if state_snapshot else {}


# Global coordinator instance
coordinator = DecisionCoordinator()
