import json

from langchain_classic.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain_classic.tools import tool

from schemas.simulation_output import SimulationOutput


# =========================================================
# 1. Core Functions
# =========================================================

def get_analysis_summary_core(analysis_output: dict) -> str:
    """
    Return the Analysis Agent's diagnosis as readable JSON.
    """

    if not isinstance(analysis_output, dict):
        raise TypeError(
            "analysis_output must be a dictionary."
        )

    if not analysis_output:
        raise ValueError(
            "Analysis output is not available."
        )

    return json.dumps(
        analysis_output,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def get_project_metrics_core(project_metrics: dict) -> str:
    """
    Return deterministic project metrics calculated
    by ProjectAnalyzer as readable JSON.
    """

    if not isinstance(project_metrics, dict):
        raise TypeError(
            "project_metrics must be a dictionary."
        )

    if not project_metrics:
        raise ValueError(
            "Project metrics are not available."
        )

    return json.dumps(
        project_metrics,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# =========================================================
# 2. Tools
# =========================================================

def build_analysis_summary_tool(analysis_output: dict):
    """
    Create a tool exposing the Analysis Agent's diagnosis
    for the current simulation run.
    """

    @tool
    def get_analysis_summary(query: str = "all") -> str:
        """
        Return the Analysis Agent's diagnosis for the current
        project: project state, root cause, bottlenecks,
        dependencies, critical tasks, schedule and workload
        signals, confidence, and data warnings.
        """
        return get_analysis_summary_core(analysis_output)

    return get_analysis_summary


def build_project_metrics_tool(project_metrics: dict):
    """
    Create a project metrics tool for the current simulation run.
    """

    @tool
    def get_project_metrics(query: str = "all") -> str:
        """
        Return calculated metrics and statistical signals for the
        current project, including issue counts, statuses, priorities,
        timing, workload, and dependency statistics when available.
        """
        return get_project_metrics_core(project_metrics)

    return get_project_metrics


# =========================================================
# 3. Tool Registry
# =========================================================

def build_simulation_tools(
    analysis_output: dict,
    project_metrics: dict,
    live_rag_tool=None,
    ground_truth_rag_tool=None,
):
    """
    Build the tools available to the Simulation Agent
    for the current project run.
    """

    tools = [
        build_analysis_summary_tool(analysis_output),
        build_project_metrics_tool(project_metrics),
    ]

    if live_rag_tool is not None:
        tools.append(live_rag_tool)

    if ground_truth_rag_tool is not None:
        tools.append(ground_truth_rag_tool)

    return tools


# =========================================================
# 4. Simulation Agent
# =========================================================

class SimulationAgent:
    """
    Propose and evaluate recovery scenarios for the current
    project, grounded in the Analysis Agent's diagnosis.
    """

    def __init__(
        self,
        llm,
        prompt,
        tools,
        verbose=False,
    ):
        self.llm = llm
        self.prompt = prompt
        self.tools = tools

        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt,
            stop_sequence=False,
        )

        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=verbose,
            handle_parsing_errors=True,
        )

    def simulate(self) -> dict:
        """
        Run the recovery simulation and return validated
        structured scenarios.
        """

        result = self.executor.invoke({
            "input": (
                "Using the Analysis Agent's diagnosis, propose and "
                "evaluate recovery scenarios for this project. "
                "Determine the recovery actions, projected delay "
                "impact when supportable, risk, tradeoffs, "
                "supporting evidence, confidence, a recommended "
                "scenario when warranted, assumptions, and data "
                "warnings. Do not invent unsupported information "
                "and do not ask the user for missing data."
            )
        })

        raw_output = result["output"]

        return self._validate_output(raw_output)

    def _validate_output(self, raw_output: str) -> dict:
        """
        Validate the final Simulation Agent JSON
        using the SimulationOutput schema.
        """

        if not raw_output:
            raise ValueError(
                "Simulation Agent returned an empty output."
            )

        cleaned_output = raw_output.strip()

        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]

        elif cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[3:]

        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]

        cleaned_output = cleaned_output.strip()

        simulation = SimulationOutput.model_validate_json(
            cleaned_output
        )

        return simulation.model_dump()