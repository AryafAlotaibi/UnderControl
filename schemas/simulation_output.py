from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RecoveryAction(BaseModel):
    action_type: Literal[
        "reassign",
        "reprioritize",
        "add_resource",
        "cut_scope",
        "extend_deadline",
        "unblock_dependency",
        "parallelize",
        "other",
    ]
    description: str
    target_tasks: List[str] = Field(default_factory=list)
    rationale: str


class SimulatedScenario(BaseModel):
    scenario_name: str

    approach_type: Literal[
        "direct_blocker_removal",
        "capacity_reallocation",
        "schedule_containment",
        "parallel_mitigation",
    ]

    basis: str

    summary: str

    actions: List[RecoveryAction] = Field(
        default_factory=list
    )

    projected_delay_days: Optional[float] = Field(
        default=None,
        ge=0
    )

    projected_risk: Literal[
        "low",
        "medium",
        "high"
    ]

    tradeoffs: str

    supporting_evidence: List[str] = Field(
        default_factory=list
    )

    confidence: Literal[
        "high",
        "medium",
        "low"
    ]


class SimulationOutput(BaseModel):
    baseline_summary: str

    scenarios: List[SimulatedScenario] = Field(
        default_factory=list
    )

    recommended_scenario: Optional[str] = None
    recommendation_rationale: Optional[str] = None

    assumptions: List[str] = Field(
        default_factory=list
    )

    data_warnings: List[str] = Field(
        default_factory=list
    )