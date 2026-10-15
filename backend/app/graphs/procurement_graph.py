"""Multi-Agent Procurement StateGraph orchestration compiled with LangGraph."""

import uuid
from typing import Any, Dict, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.graphs.edges import route_after_intake
from app.graphs.nodes import (
    approval_gate_node,
    discovery_node,
    explanation_node,
    finalization_node,
    intake_node,
    parallel_eval_node,
    quotation_node,
    scoring_node,
)
from app.graphs.state import ProcurementEvaluationState


def build_procurement_graph(checkpointer=None):
    """Assemble and compile the end-to-end procurement evaluation StateGraph."""
    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(ProcurementEvaluationState)

    # Register workflow nodes
    builder.add_node("intake", intake_node)
    builder.add_node("discovery", discovery_node)
    builder.add_node("quotation", quotation_node)
    builder.add_node("parallel_eval", parallel_eval_node)
    builder.add_node("scoring", scoring_node)
    builder.add_node("explanation", explanation_node)
    builder.add_node("approval_gate", approval_gate_node)
    builder.add_node("finalization", finalization_node)

    # Edge connections
    builder.add_edge(START, "intake")
    builder.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "discovery": "discovery",
            END: END,
        },
    )
    builder.add_edge("discovery", "quotation")
    builder.add_edge("quotation", "parallel_eval")
    builder.add_edge("parallel_eval", "scoring")
    builder.add_edge("scoring", "explanation")
    builder.add_edge("explanation", "approval_gate")
    builder.add_edge("approval_gate", "finalization")
    builder.add_edge("finalization", END)

    return builder.compile(checkpointer=checkpointer)


# Singleton workflow graph instance for shared evaluation sessions
evaluation_graph = build_procurement_graph()


def execute_evaluation(
    initial_state: ProcurementEvaluationState,
    thread_id: Optional[str] = None,
    graph=None,
) -> Dict[str, Any]:
    """Execute the procurement evaluation graph until completion or human interrupt gate."""
    target_graph = graph or evaluation_graph
    t_id = thread_id or initial_state.get("thread_id") or str(uuid.uuid4())
    config = {"configurable": {"thread_id": t_id}}

    state_with_thread = {**initial_state, "thread_id": t_id}
    return target_graph.invoke(state_with_thread, config=config)


def resume_evaluation(
    thread_id: str,
    approval_data: Dict[str, Any],
    graph=None,
) -> Dict[str, Any]:
    """Resume execution of an interrupted evaluation with human officer approval decision."""
    target_graph = graph or evaluation_graph
    config = {"configurable": {"thread_id": thread_id}}

    resume_command = Command(resume=approval_data)
    return target_graph.invoke(resume_command, config=config)
