import pandas as pd

from agents.simulation_agent import (
    SimulationAgent,
    build_simulation_tools,
)

from llm.model import create_agent_llm
from prompts.simulation_prompt import simulation_prompt
from schemas.analysis_output import AnalysisOutput

from rag.build_rag import build_live_rag
from rag.retriever import build_live_rag_tool


# =========================================================
# Sample Project
# =========================================================

project_df = pd.DataFrame(
    [
        {
            "issue_key": "UC-1",
            "type": "Task",
            "status": "Blocked",
            "priority": "High",
            "assignee_id": "user_1",
            "dependency": "UC-2",
            "resolution": None,
            "resolution_date": None,
            "text": (
                "High priority task blocked by UC-2."
            ),
        },
        {
            "issue_key": "UC-2",
            "type": "Task",
            "status": "In Progress",
            "priority": "Medium",
            "assignee_id": "user_2",
            "dependency": None,
            "resolution": None,
            "resolution_date": None,
            "text": (
                "Task required by UC-1 and currently "
                "in progress."
            ),
        },
        {
            "issue_key": "UC-3",
            "type": "Task",
            "status": "Done",
            "priority": "Low",
            "assignee_id": "user_2",
            "dependency": None,
            "resolution": "Fixed",
            "resolution_date": "2026-09-10",
            "text": "Completed project task.",
        },
    ]
)


# =========================================================
# Sample AnalysisOutput
# =========================================================

analysis_output = AnalysisOutput(
    project_state="delayed",

    estimated_delay_days=None,

    root_cause={
        "category": "dependency",
        "summary": (
            "A high-priority task is blocked."
        ),
        "explanation": (
            "UC-1 is blocked by UC-2 "
            "and remains unfinished."
        ),
        "affected_tasks": [
            "UC-1"
        ],
    },

    bottlenecks=[
        {
            "task_id": "UC-1",
            "summary": (
                "Blocked high-priority task."
            ),
            "status": "Blocked",
            "priority": "High",
            "assignee": "user_1",
            "reason": (
                "The task depends on UC-2."
            ),
            "impact": (
                "The task cannot progress."
            ),
            "affected_tasks": [
                "UC-1"
            ],
        }
    ],

    dependencies=[
        {
            "blocked_task": "UC-1",
            "depends_on": "UC-2",
            "impact": (
                "UC-1 cannot progress until "
                "the dependency is resolved."
            ),
            "affected_tasks": [
                "UC-1"
            ],
        }
    ],

    critical_tasks=[
        {
            "task_id": "UC-1",
            "reason": (
                "High-priority blocked task."
            ),
        }
    ],

    schedule_signals={
        "blocked_tasks": 1,
        "unfinished_high_priority_tasks": 1,
    },

    workload_signals=[],

    evidence=[
        "UC-1 has status Blocked.",
        "UC-1 has High priority.",
        "UC-1 depends on UC-2.",
    ],

    confidence="high",

    data_warnings=[],
)


# =========================================================
# Build Live RAG
# =========================================================

print("Building Live RAG...")

live_collection = build_live_rag(
    project_df
)

live_rag_tool = build_live_rag_tool(
    live_collection
)

print("Live RAG created successfully.")


# =========================================================
# Build Simulation Agent
# =========================================================

llm = create_agent_llm()

tools = build_simulation_tools(
    project_df=project_df,
    live_rag_tool=live_rag_tool,
)

agent = SimulationAgent(
    llm=llm,
    prompt=simulation_prompt,
    tools=tools,
    analysis_output=analysis_output,
    verbose=False,
)


# =========================================================
# Basic Checks
# =========================================================

print("\nSimulationAgent created successfully.")

print(
    "simulate method exists:",
    hasattr(agent, "simulate"),
)

print(
    "tools:",
    [tool.name for tool in tools],
)


# =========================================================
# Run Simulation Agent
# =========================================================

print("\nRunning Simulation Agent...\n")

try:
    result = agent.simulate()

    print(
        "Simulation completed successfully."
    )

    print("\nResult:")
    print(result)

except Exception as error:
    print("\nSimulation Agent failed.")

    print(
        type(error).__name__
    )

    print(error)