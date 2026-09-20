import pandas as pd

from simulation.simulator import (
    SimulationError,
    simulate_strategy_core,
)


# =========================================================
# Sample project
# =========================================================

project_df = pd.DataFrame(
    [
        {
            "issue_key": "UC-1",
            "status": "Blocked",
            "priority": "High",
            "assignee_id": "user_1",
            "dependency": "UC-2",
            "resolution": None,
            "resolution_date": None,
        },
        {
            "issue_key": "UC-2",
            "status": "In Progress",
            "priority": "Medium",
            "assignee_id": "user_2",
            "dependency": None,
            "resolution": None,
            "resolution_date": None,
        },
        {
            "issue_key": "UC-3",
            "status": "Done",
            "priority": "Low",
            "assignee_id": "user_2",
            "dependency": None,
            "resolution": "Fixed",
            "resolution_date": "2026-09-10",
        },
    ]
)


# =========================================================
# Helper
# =========================================================

def run_test(
    name: str,
    strategy: dict,
) -> None:

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    try:
        result = simulate_strategy_core(
            project_df=project_df,
            strategy=strategy,
        )

        print("Status:")
        print(result["status"])

        print("\nModified tasks:")
        print(result["modified_tasks"])

        print("\nComparison:")
        print(result["comparison"])

    except SimulationError as error:
        print("SimulationError:")
        print(error)


# =========================================================
# Test 1: Resource Reassignment
# =========================================================

resource_reassignment = {
    "type": "resource_reassignment",
    "description": (
        "Reassign the blocked task "
        "to an existing team member."
    ),
    "target_tasks": ["UC-1"],
    "changes": {
        "assignee_id": {
            "to": "user_2"
        }
    },
}


# =========================================================
# Test 2: Reprioritization
# =========================================================

reprioritization = {
    "type": "reprioritization",
    "description": (
        "Change the task priority "
        "to an existing project priority."
    ),
    "target_tasks": ["UC-2"],
    "changes": {
        "priority": {
            "to": "High"
        }
    },
}


# =========================================================
# Test 3: Dependency Resolution
# =========================================================

dependency_resolution = {
    "type": "dependency_resolution",
    "description": (
        "Remove the dependency from "
        "the blocked task."
    ),
    "target_tasks": ["UC-1"],
    "changes": {
        "dependency": {
            "action": "remove"
        }
    },
}


# =========================================================
# Test 4: Invalid Priority
# =========================================================

invalid_priority = {
    "type": "reprioritization",
    "description": (
        "Test an invalid priority."
    ),
    "target_tasks": ["UC-2"],
    "changes": {
        "priority": {
            "to": "SUPER_URGENT"
        }
    },
}


# =========================================================
# Run tests
# =========================================================

run_test(
    "TEST 1 - RESOURCE REASSIGNMENT",
    resource_reassignment,
)

run_test(
    "TEST 2 - REPRIORITIZATION",
    reprioritization,
)

run_test(
    "TEST 3 - DEPENDENCY RESOLUTION",
    dependency_resolution,
)

run_test(
    "TEST 4 - INVALID PRIORITY",
    invalid_priority,
)