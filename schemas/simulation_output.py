from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """
    A recovery action proposed by the Simulation Agent.
    """

    type: str

    description: str

    target_tasks: List[str] = Field(
        default_factory=list
    )

    changes: Dict[str, Any] = Field(
        default_factory=dict
    )


class SimulationResult(BaseModel):
    """
    Result returned by the deterministic simulator
    for one recovery strategy.
    """

    strategy: Strategy

    status: Literal[
        "feasible",
        "partially_feasible",
        "infeasible",
    ]

    expected_effect: str

    affected_tasks: List[str] = Field(
        default_factory=list
    )

    modified_tasks: List[str] = Field(
        default_factory=list
    )

    before: Dict[str, Any] = Field(
        default_factory=dict
    )

    after: Dict[str, Any] = Field(
        default_factory=dict
    )

    comparison: Dict[str, Any] = Field(
        default_factory=dict
    )

    resource_impact: Literal[
        "low",
        "medium",
        "high",
        "unknown",
    ]

    risk: Literal[
        "low",
        "medium",
        "high",
        "unknown",
    ]

    assumptions: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )


class StrategyComparison(BaseModel):
    """
    Comparison used by the Simulation Agent when
    selecting between simulated recovery strategies.
    """

    strategy_type: str

    effectiveness: str

    feasibility: str

    risk: str

    resource_impact: str

    summary: str


class SimulationOutput(BaseModel):
    """
    Final structured output of the Simulation Agent.

    This output is designed for direct consumption by
    the UnderControl dashboard.
    """

    identified_problem: str

    candidate_strategies: List[Strategy] = Field(
        default_factory=list
    )

    simulated_strategies: List[SimulationResult] = Field(
        default_factory=list
    )

    comparison: List[StrategyComparison] = Field(
        default_factory=list
    )

    selected_strategy: Optional[Strategy] = None

    selected_simulation: Optional[SimulationResult] = None

    expected_delay_reduction: Optional[float] = None

    explanation: str

    assumptions: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )