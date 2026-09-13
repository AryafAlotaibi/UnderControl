from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RootCause(BaseModel):
    category: str
    summary: str
    explanation: str
    affected_tasks: List[str] = Field(default_factory=list)


class Bottleneck(BaseModel):
    task_id: str
    summary: str
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reason: str
    impact: str


class Dependency(BaseModel):
    blocked_task: str
    depends_on: str
    impact: str


class CriticalTask(BaseModel):
    task_id: str
    reason: str


class ScheduleSignals(BaseModel):
    overdue_tasks: Optional[int] = None
    blocked_tasks: Optional[int] = None
    unfinished_high_priority_tasks: Optional[int] = None


class WorkloadSignal(BaseModel):
    assignee: Optional[str] = None
    issue: str
    affected_tasks: List[str] = Field(default_factory=list)


class AnalysisOutput(BaseModel):
    project_state: Literal[
        "healthy",
        "delayed",
        "uncertain"
    ]

    estimated_delay_days: Optional[float] = Field(
        default=None,
        ge=0
    )

    root_cause: Optional[RootCause] = None

    bottlenecks: List[Bottleneck] = Field(
        default_factory=list
    )

    dependencies: List[Dependency] = Field(
        default_factory=list
    )

    critical_tasks: List[CriticalTask] = Field(
        default_factory=list
    )

    schedule_signals: ScheduleSignals = Field(
        default_factory=ScheduleSignals
    )

    workload_signals: List[WorkloadSignal] = Field(
        default_factory=list
    )

    evidence: List[str] = Field(
        default_factory=list
    )

    confidence: Literal[
        "high",
        "medium",
        "low"
    ]

    data_warnings: List[str] = Field(
        default_factory=list
    )