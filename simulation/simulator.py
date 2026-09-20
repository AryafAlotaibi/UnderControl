from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from analysis.project_analyzer import ProjectAnalyzer


class SimulationError(Exception):
    """Raised when a simulation cannot be performed safely."""


# =========================================================
# Metrics
# =========================================================

def _calculate_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate deterministic project metrics using the same
    ProjectAnalyzer used by the Analysis Agent.
    """

    analyzer = ProjectAnalyzer()
    prepared = analyzer.prepare_project(df)

    return prepared["metrics"]


# =========================================================
# Strategy Validation
# =========================================================

SUPPORTED_OPERATIONS = {
    "resource_reassignment",
    "dependency_resolution",
    "reprioritization",
}


def _validate_strategy(strategy: dict) -> None:
    if not isinstance(strategy, dict):
        raise SimulationError(
            "Strategy must be a dictionary."
        )

    if not strategy:
        raise SimulationError(
            "Strategy cannot be empty."
        )

    strategy_type = strategy.get("type")

    if not strategy_type:
        raise SimulationError(
            "Strategy must contain a 'type'."
        )

    if strategy_type not in SUPPORTED_OPERATIONS:
        raise SimulationError(
            f"Unsupported strategy type: {strategy_type}"
        )


# =========================================================
# Helpers
# =========================================================

def _ensure_column(
    df: pd.DataFrame,
    column: str,
) -> None:
    if column not in df.columns:
        raise SimulationError(
            f"Required project column '{column}' is not available."
        )


def _get_target_tasks(
    df: pd.DataFrame,
    strategy: dict,
) -> list[str]:
    _ensure_column(df, "issue_key")

    target_tasks = strategy.get(
        "target_tasks",
        [],
    )

    if not isinstance(target_tasks, list):
        raise SimulationError(
            "'target_tasks' must be a list."
        )

    target_tasks = [
        str(task).strip()
        for task in target_tasks
        if str(task).strip()
    ]

    if not target_tasks:
        raise SimulationError(
            "Strategy must specify at least one target task."
        )

    existing_tasks = set(
        df["issue_key"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_tasks = [
        task
        for task in target_tasks
        if task not in existing_tasks
    ]

    if missing_tasks:
        raise SimulationError(
            "Target task(s) do not exist in the current project: "
            + ", ".join(missing_tasks)
        )

    return target_tasks


# =========================================================
# Strategy: Resource Reassignment
# =========================================================

def _apply_resource_reassignment(
    df: pd.DataFrame,
    strategy: dict,
) -> list[str]:
    _ensure_column(df, "issue_key")
    _ensure_column(df, "assignee_id")

    target_tasks = _get_target_tasks(
        df,
        strategy,
    )

    changes = strategy.get(
        "changes",
        {},
    )

    assignee_change = changes.get(
        "assignee_id"
    )

    if not isinstance(
        assignee_change,
        dict,
    ):
        raise SimulationError(
            "resource_reassignment requires "
            "'changes.assignee_id'."
        )

    new_assignee = assignee_change.get("to")

    if new_assignee is None:
        raise SimulationError(
            "resource_reassignment requires "
            "'changes.assignee_id.to'."
        )

    new_assignee = str(
        new_assignee
    ).strip()

    if not new_assignee:
        raise SimulationError(
            "New assignee cannot be empty."
        )

    existing_assignees = set(
        df["assignee_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if new_assignee not in existing_assignees:
        raise SimulationError(
            f"Target assignee '{new_assignee}' "
            "does not exist in the current project."
        )

    mask = df["issue_key"].astype(str).isin(
        target_tasks
    )

    current_values = (
        df.loc[mask, "assignee_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    changed_index = current_values[
        current_values != new_assignee
    ].index

    if len(changed_index) == 0:
        raise SimulationError(
            "The strategy does not change the assignee "
            "of the target task(s)."
        )

    df.loc[
        changed_index,
        "assignee_id"
    ] = new_assignee

    modified_tasks = (
        df.loc[changed_index, "issue_key"]
        .astype(str)
        .tolist()
    )

    return modified_tasks


# =========================================================
# Strategy: Reprioritization
# =========================================================

def _apply_reprioritization(
    df: pd.DataFrame,
    strategy: dict,
) -> list[str]:
    _ensure_column(df, "issue_key")
    _ensure_column(df, "priority")

    target_tasks = _get_target_tasks(
        df,
        strategy,
    )

    changes = strategy.get(
        "changes",
        {},
    )

    priority_change = changes.get(
        "priority"
    )

    if not isinstance(
        priority_change,
        dict,
    ):
        raise SimulationError(
            "reprioritization requires "
            "'changes.priority'."
        )

    new_priority = priority_change.get(
        "to"
    )

    if new_priority is None:
        raise SimulationError(
            "reprioritization requires "
            "'changes.priority.to'."
        )

    new_priority = str(
        new_priority
    ).strip()

    if not new_priority:
        raise SimulationError(
            "New priority cannot be empty."
        )

    existing_priorities = set(
        df["priority"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if new_priority not in existing_priorities:
        raise SimulationError(
            f"Target priority '{new_priority}' "
            "does not exist in the current project."
        )

    mask = df["issue_key"].astype(str).isin(
        target_tasks
    )

    current_values = (
        df.loc[mask, "priority"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    changed_index = current_values[
        current_values != new_priority
    ].index

    if len(changed_index) == 0:
        raise SimulationError(
            "The strategy does not change the priority "
            "of the target task(s)."
        )

    df.loc[
        changed_index,
        "priority"
    ] = new_priority

    modified_tasks = (
        df.loc[changed_index, "issue_key"]
        .astype(str)
        .tolist()
    )

    return modified_tasks


# =========================================================
# Strategy: Dependency Resolution
# =========================================================

def _apply_dependency_resolution(
    df: pd.DataFrame,
    strategy: dict,
) -> list[str]:
    _ensure_column(df, "issue_key")

    if "dependency" not in df.columns:
        raise SimulationError(
            "Current project does not contain "
            "dependency information."
        )

    target_tasks = _get_target_tasks(
        df,
        strategy,
    )

    changes = strategy.get(
        "changes",
        {},
    )

    dependency_change = changes.get(
        "dependency"
    )

    if not isinstance(
        dependency_change,
        dict,
    ):
        raise SimulationError(
            "dependency_resolution requires "
            "'changes.dependency'."
        )

    action = dependency_change.get(
        "action"
    )

    if action != "remove":
        raise SimulationError(
            "dependency_resolution currently supports "
            "only changes.dependency.action='remove'."
        )

    mask = df["issue_key"].astype(str).isin(
        target_tasks
    )

    current_dependencies = df.loc[
        mask,
        "dependency"
    ]

    has_dependency = (
        current_dependencies.notna()
        & current_dependencies
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )

    changed_index = current_dependencies[
        has_dependency
    ].index

    if len(changed_index) == 0:
        raise SimulationError(
            "The target task(s) do not have "
            "a dependency to remove."
        )

    df.loc[
        changed_index,
        "dependency"
    ] = None

    modified_tasks = (
        df.loc[changed_index, "issue_key"]
        .astype(str)
        .tolist()
    )

    return modified_tasks


# =========================================================
# Apply Strategy
# =========================================================

def _apply_strategy(
    df: pd.DataFrame,
    strategy: dict,
) -> list[str]:
    strategy_type = strategy["type"]

    if strategy_type == "resource_reassignment":
        return _apply_resource_reassignment(
            df,
            strategy,
        )

    if strategy_type == "reprioritization":
        return _apply_reprioritization(
            df,
            strategy,
        )

    if strategy_type == "dependency_resolution":
        return _apply_dependency_resolution(
            df,
            strategy,
        )

    raise SimulationError(
        f"Unsupported strategy type: {strategy_type}"
    )


# =========================================================
# Compare Metrics
# =========================================================

def _compare_metrics(
    before: dict,
    after: dict,
) -> dict:
    comparison: Dict[str, Any] = {}

    # -------------------------
    # Schedule signals
    # -------------------------

    before_schedule = before.get(
        "schedule_signals",
        {}
    )

    after_schedule = after.get(
        "schedule_signals",
        {}
    )

    schedule_changes = {}

    for key in (
        "overdue_tasks",
        "blocked_tasks",
        "unfinished_high_priority_tasks",
    ):
        before_value = before_schedule.get(
            key
        )

        after_value = after_schedule.get(
            key
        )

        if (
            before_value is not None
            and after_value is not None
        ):
            schedule_changes[key] = {
                "before": before_value,
                "after": after_value,
                "delta": after_value - before_value,
            }

    comparison["schedule_signals"] = (
        schedule_changes
    )

    # -------------------------
    # Workload
    # -------------------------

    before_workload = before.get(
        "tasks_per_assignee",
        {}
    )

    after_workload = after.get(
        "tasks_per_assignee",
        {}
    )

    all_assignees = set(
        before_workload
    ) | set(
        after_workload
    )

    workload_changes = {}

    for assignee in all_assignees:
        before_count = int(
            before_workload.get(
                assignee,
                0,
            )
        )

        after_count = int(
            after_workload.get(
                assignee,
                0,
            )
        )

        if before_count != after_count:
            workload_changes[assignee] = {
                "before": before_count,
                "after": after_count,
                "delta": after_count - before_count,
            }

    comparison["tasks_per_assignee"] = (
        workload_changes
    )

    # -------------------------
    # Dependency count
    # -------------------------

    before_dependencies = before.get(
        "dependency_count"
    )

    after_dependencies = after.get(
        "dependency_count"
    )

    if (
        before_dependencies is not None
        and after_dependencies is not None
    ):
        comparison["dependency_count"] = {
            "before": before_dependencies,
            "after": after_dependencies,
            "delta": (
                after_dependencies
                - before_dependencies
            ),
        }

    # -------------------------
    # Priority distribution
    # -------------------------

    comparison["priority_distribution"] = {
        "before": before.get(
            "priority_distribution",
            {}
        ),
        "after": after.get(
            "priority_distribution",
            {}
        ),
    }

    return comparison


# =========================================================
# Main Simulation
# =========================================================

def simulate_strategy_core(
    project_df: pd.DataFrame,
    strategy: dict,
) -> dict:
    if not isinstance(
        project_df,
        pd.DataFrame,
    ):
        raise TypeError(
            "project_df must be a pandas DataFrame."
        )

    _validate_strategy(strategy)

    before_df = project_df.copy(
        deep=True
    )

    before_metrics = _calculate_metrics(
        before_df
    )

    after_df = project_df.copy(
        deep=True
    )

    modified_tasks = _apply_strategy(
        after_df,
        strategy,
    )

    after_metrics = _calculate_metrics(
        after_df
    )

    comparison = _compare_metrics(
        before_metrics,
        after_metrics,
    )

    affected_tasks = modified_tasks
    status = "feasible"
    warnings = []

    if not affected_tasks:
        status = "infeasible"

        warnings.append(
            "The strategy did not modify any project task."
        )

    return {
        "strategy": strategy,

        "status": status,

        "expected_effect": (
            "The strategy was applied to a copy of the "
            "current project and the supported project "
            "metrics were recalculated."
        ),

        "affected_tasks": affected_tasks,

        "modified_tasks": modified_tasks,

        "before": before_metrics,

        "after": after_metrics,

        "comparison": comparison,

        "resource_impact": _estimate_resource_impact(
            strategy
        ),

        "risk": _estimate_risk(
            strategy,
            comparison,
        ),

        "assumptions": [
            (
                "The simulation modifies a copy "
                "of the current project only."
            ),
            (
                "The original project data "
                "is not modified."
            ),
            (
                "Only changes explicitly represented "
                "by the strategy are applied."
            ),
            (
                "Metrics are recalculated "
                "using ProjectAnalyzer."
            ),
            "No productivity model is assumed.",
            "No resource-capacity model is assumed.",
            "No hiring or onboarding model is assumed.",
            "No schedule-duration prediction is assumed.",
            "No completion-date prediction is assumed.",
        ],

        "warnings": warnings,
    }


# =========================================================
# Deterministic Risk / Impact
# =========================================================

def _estimate_resource_impact(
    strategy: dict,
) -> str:
    return "unknown"


def _estimate_risk(
    strategy: dict,
    comparison: dict,
) -> str:
    return "unknown"