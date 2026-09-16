import json

from langchain_classic.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain_classic.tools import tool

from schemas.analysis_output import AnalysisOutput


# =========================================================
# 1. Core Functions
# =========================================================

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

def build_project_metrics_tool(project_metrics: dict):
    """
    Create a project metrics tool for the current analysis run.
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

def build_analysis_tools(
    project_metrics: dict,
    live_rag_tool=None,
    ground_truth_rag_tool=None,
):
    """
    Build the tools available to the Analysis Agent
    for the current project run.
    """

    tools = [
        build_project_metrics_tool(project_metrics)
    ]

    if live_rag_tool is not None:
        tools.append(live_rag_tool)

    if ground_truth_rag_tool is not None:
        tools.append(ground_truth_rag_tool)

    return tools


# =========================================================
# 4. Analysis Agent
# =========================================================

class AnalysisAgent:
    """
    Diagnose the current project using project metrics
    and available RAG tools.
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
            verbose=False, #Back to True for debugging !!! Return to False for production
            handle_parsing_errors=True,
        )

    def analyze(self) -> dict:
        """
        Run project diagnosis and return validated
        structured analysis.
        """

        result = self.executor.invoke({
            "input": (
                "Analyze the current project using the available "
                "tools and evidence. Determine the project state, "
                "estimated delay, root cause, bottlenecks, "
                "dependencies, critical tasks, schedule signals, "
                "workload signals, supporting evidence, confidence, "
                "and data warnings. "
                "Do not invent unsupported information and do not "
                "ask the user for missing data."
            )
        })

        raw_output = result["output"]

        return self._validate_output(raw_output)

    def _validate_output(self, raw_output: str) -> dict:
        """
        Validate the final Analysis Agent JSON
        using the AnalysisOutput schema.
        """

        if not raw_output:
            raise ValueError(
                "Analysis Agent returned an empty output."
            )

        cleaned_output = raw_output.strip()

        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]

        elif cleaned_output.startswith("```"):
            cleaned_output = cleaned_output[3:]

        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]

        cleaned_output = cleaned_output.strip()

        analysis = AnalysisOutput.model_validate_json(
            cleaned_output
        )

        return analysis.model_dump()