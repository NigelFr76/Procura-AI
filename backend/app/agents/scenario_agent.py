"""Agent 7: Scenario Simulation Agent for What-If parameter shifts and rank displacement analysis."""

from app.schemas.scenario import (
    ScenarioRunInput,
    ScenarioRunResult,
)
from app.services.scenarios.scenario_engine import ScenarioSimulationEngine


class ScenarioSimulationAgent:
    """Specialized agent coordinating What-If parameter overrides and causal shift explanations."""

    @classmethod
    def run_simulation(cls, input_data: ScenarioRunInput) -> ScenarioRunResult:
        """Execute deterministic simulation and synthesize audit explanation."""
        # Execute authoritative pure-Python scenario engine
        return ScenarioSimulationEngine.execute_scenario(input_data)
