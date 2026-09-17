from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """
    A recovery action that can be tested by the deterministic simulator.
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
    Result returned by the deterministic simulator for one strategy.
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
    Comparison used when evaluating simulated recovery strategies.
    """

    strategy_type: str
    effectiveness: str
    feasibility: str
    risk: str
    resource_impact: str
    summary: str


class RecoveryStep(BaseModel):
    """
    One evidence-based execution step in the final recovery order.

    Multiple task IDs may appear in the same step when the available
    dependency evidence supports progressing them in parallel.
    """

    step: int

    task_ids: List[str] = Field(
        default_factory=list
    )

    action: str


class SimulationOutput(BaseModel):
    """
    Final structured output of the Simulation Agent.

    The output contains both:
    1. deterministic what-if simulation results, and
    2. an evidence-based recovery plan for the user.
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

    # Final user-facing recovery guidance. This is intentionally separate from
    # selected_strategy because the practical recovery path may include actions
    # outside the simulator's supported strategy types.
    recovery_plan_summary: str = ""

    recovery_execution_order: List[RecoveryStep] = Field(
        default_factory=list
    )

    recovery_order_reason: str = ""

    assumptions: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )
