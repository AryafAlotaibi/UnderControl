import json

from langchain_classic.agents import (
    AgentExecutor,
    create_react_agent,
)
from langchain_classic.tools import tool

from schemas.analysis_output import AnalysisOutput
from schemas.simulation_output import SimulationOutput
from simulation.simulator import simulate_strategy_core


# =========================================================
# 1. Simulation Tool
# =========================================================


def build_simulate_strategy_tool(project_df):
    """Build the deterministic simulator tool for this project."""

    @tool
    def simulate_strategy(strategy: str) -> str:
        """
        Simulate one recovery strategy against a copy of the
        current project.

        Input must be a JSON object encoded as a string.
        """

        try:
            payload = json.loads(strategy)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(
                "strategy must be a valid JSON object."
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "strategy must be a JSON object."
            )

        try:
            result = simulate_strategy_core(
                project_df=project_df,
                strategy=payload,
            )

        except Exception as exc:
            # A candidate selected by the LLM may be invalid for the
            # current project. Return the simulator rejection to the
            # agent so it can revise or discard the candidate instead
            # of crashing the whole Simulation Agent run.
            return json.dumps(
                {
                    "simulation_error": str(exc),
                    "strategy": payload,
                },
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        return json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return simulate_strategy


# =========================================================
# 2. Tool Registry
# =========================================================


def build_simulation_tools(
    project_df,
    live_rag_tool=None,
):
    """Build the tools available to the Simulation Agent."""

    tools = [
        build_simulate_strategy_tool(project_df)
    ]

    if live_rag_tool is not None:
        tools.append(live_rag_tool)

    return tools


# =========================================================
# 3. Simulation Agent
# =========================================================


class SimulationAgent:
    """
    Review the Analysis Agent diagnosis, choose evidence-supported
    recovery strategies when appropriate, simulate them, compare the
    real results, and produce final project guidance.

    Strategy selection belongs to the LLM reasoning layer.
    Strategy execution and metric recalculation remain deterministic
    inside the simulator.
    """

    def __init__(
        self,
        llm,
        prompt,
        tools,
        analysis_output,
        verbose=False,
    ):
        self.llm = llm
        self.prompt = prompt

        if isinstance(analysis_output, AnalysisOutput):
            self.analysis_output = analysis_output
        elif isinstance(analysis_output, dict):
            self.analysis_output = AnalysisOutput.model_validate(
                analysis_output
            )
        else:
            raise TypeError(
                "analysis_output must be an AnalysisOutput "
                "object or dictionary."
            )

        # Healthy and uncertain projects still use the Simulation Agent
        # to produce a conclusion and recommended direction, but they are
        # not allowed to execute recovery what-if strategies.
        self.tools = list(tools)

        if self.analysis_output.project_state != "delayed":
            self.tools = [
                current_tool
                for current_tool in self.tools
                if getattr(current_tool, "name", None)
                != "simulate_strategy"
            ]

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
            max_iterations=8,
            early_stopping_method="force",
        )

    # =====================================================
    # Tool Helpers
    # =====================================================

    def _get_tool(self, tool_name):
        for current_tool in self.tools:
            if getattr(current_tool, "name", None) == tool_name:
                return current_tool
        return None

    def _collect_relevant_task_ids(self):
        """Collect task IDs already identified by AnalysisOutput."""

        analysis = self.analysis_output.model_dump()
        task_ids = []

        root_cause = analysis.get("root_cause") or {}
        task_ids.extend(root_cause.get("affected_tasks") or [])

        for item in analysis.get("bottlenecks") or []:
            if item.get("task_id"):
                task_ids.append(item["task_id"])
            task_ids.extend(item.get("affected_tasks") or [])

        for item in analysis.get("dependencies") or []:
            if item.get("blocked_task"):
                task_ids.append(item["blocked_task"])
            if item.get("depends_on"):
                task_ids.append(item["depends_on"])
            task_ids.extend(item.get("affected_tasks") or [])

        for item in analysis.get("critical_tasks") or []:
            if item.get("task_id"):
                task_ids.append(item["task_id"])

        for item in analysis.get("workload_signals") or []:
            task_ids.extend(item.get("related_tasks") or [])

        cleaned = []
        seen = set()

        for task_id in task_ids:
            value = str(task_id).strip()
            if value and value not in seen:
                cleaned.append(value)
                seen.add(value)

        return cleaned

    def _get_live_project_context(self):
        """
        Retrieve exact current-project records for tasks already
        identified by the Analysis Agent.
        """

        live_tool = self._get_tool(
            "search_live_project"
        )

        if live_tool is None:
            return "Live project search is not available."

        task_ids = self._collect_relevant_task_ids()

        try:
            if task_ids:
                request = json.dumps(
                    {
                        "mode": "filter",
                        "issue_key": task_ids,
                    },
                    ensure_ascii=False,
                )

                return live_tool.invoke(
                    {"request": request}
                )

            root_cause = self.analysis_output.root_cause

            if root_cause is not None:
                query = (
                    root_cause.summary
                    or root_cause.explanation
                )
            else:
                query = (
                    "current project status, progress, workload, "
                    "dependencies, and notable task patterns"
                )

            request = json.dumps(
                {
                    "mode": "semantic",
                    "query": query,
                },
                ensure_ascii=False,
            )

            return live_tool.invoke(
                {"request": request}
            )

        except Exception as exc:
            return (
                "Live project context could not be retrieved: "
                f"{exc}"
            )

    # =====================================================
    # Main Agent Run
    # =====================================================

    def simulate(self) -> dict:
        """Evaluate the project and produce final simulation guidance."""

        analysis_json = self.analysis_output.model_dump_json(
            indent=2
        )

        live_context = self._get_live_project_context()

        if self.analysis_output.project_state == "delayed":
            state_instruction = (
                "The project is classified as delayed. Decide which of "
                "the supported recovery strategies are actually relevant "
                "to the diagnosed problem. Do not test a strategy merely "
                "because it exists. You may test more than one strategy "
                "when the evidence supports multiple reasonable alternatives. "
                "Every candidate must be simulated before it is evaluated "
                "or selected."
            )
        else:
            state_instruction = (
                "The project is not classified as delayed. Do not generate "
                "or simulate recovery strategies. Review the AnalysisOutput "
                "and current-project context, then produce the conclusion "
                "and recommended direction without recovery what-if testing."
            )

        result = self.executor.invoke(
            {
                "input": (
                    "Use the AnalysisOutput as the starting diagnosis.\n\n"
                    "AnalysisOutput:\n"
                    f"{analysis_json}\n\n"
                    "Live Project Context:\n"
                    f"{live_context}\n\n"
                    "Project-State Instruction:\n"
                    f"{state_instruction}\n\n"
                    "For delayed projects, strategy selection is your "
                    "reasoning responsibility. Use current-project evidence "
                    "to decide which supported strategy or strategies are "
                    "worth testing, then rely only on real simulator results "
                    "to judge feasibility and effectiveness.\n\n"
                    "Never invent delay reduction, productivity, resource "
                    "capacity, cost, completion dates, or days saved."
                )
            }
        )

        return self._validate_output(
            result.get("output")
        )

    # =====================================================
    # Output Validation
    # =====================================================

    def _validate_output(
        self,
        raw_output,
    ) -> dict:
        """Validate the final SimulationOutput."""

        if not raw_output:
            raise ValueError(
                "Simulation Agent returned an empty output."
            )

        cleaned_output = str(raw_output).strip()

        if cleaned_output.startswith("Final Answer:"):
            cleaned_output = cleaned_output[
                len("Final Answer:"):
            ].strip()

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
