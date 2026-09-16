import json

from langchain_classic.agents import (
    create_react_agent,
    AgentExecutor,
)

from langchain_classic.tools import tool

from schemas.analysis_output import AnalysisOutput
from schemas.simulation_output import SimulationOutput

from simulation.simulator import (
    simulate_strategy_core,
)


# =========================================================
# 1. Simulation Tool
# =========================================================

def build_simulate_strategy_tool(project_df):
    """
    Build the deterministic simulation tool for the
    current project.
    """

    @tool
    def simulate_strategy(
        strategy: str,
    ) -> str:
        """
        Evaluate a proposed recovery strategy against
        a copy of the current project state.

        The strategy must be a JSON object.
        """

        try:
            payload = json.loads(strategy)

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            raise ValueError(
                "strategy must be a valid JSON object."
            )

        if not isinstance(payload, dict):
            raise ValueError(
                "strategy must be a JSON object."
            )

        result = simulate_strategy_core(
            project_df=project_df,
            strategy=payload,
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
    """
    Build the tools available to the Simulation Agent.
    """

    tools = [
        build_simulate_strategy_tool(
            project_df
        )
    ]

    if live_rag_tool is not None:
        tools.append(
            live_rag_tool
        )

    return tools

# =========================================================
# 3. Simulation Agent
# =========================================================

class SimulationAgent:
    """
    Generates, simulates, compares, and selects
    recovery actions based on the Analysis Agent diagnosis.
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
        self.tools = tools

        if isinstance(
            analysis_output,
            AnalysisOutput,
        ):
            self.analysis_output = analysis_output

        elif isinstance(
            analysis_output,
            dict,
        ):
            self.analysis_output = (
                AnalysisOutput.model_validate(
                    analysis_output
                )
            )

        else:
            raise TypeError(
                "analysis_output must be an "
                "AnalysisOutput object or dictionary."
            )

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
            max_iterations=6,
            early_stopping_method="force",


        )

        def simulate(self) -> dict:
            """
            Generate and evaluate recovery strategies
            using the AnalysisOutput as the starting diagnosis.
            """

            analysis_json = (
                self.analysis_output.model_dump_json(
                    indent=2
                )
            )

            result = self.executor.invoke(
                {
                    "input": (
                        "Use the AnalysisOutput below as the "
                        "starting diagnosis.\n\n"

                        "AnalysisOutput:\n"
                        f"{analysis_json}\n\n"

                        "Your task is to determine what actions "
                        "the project manager can take to address "
                        "the diagnosed problem.\n\n"

                        "Generate 2 to 4 plausible recovery "
                        "strategies based only on supported "
                        "current-project evidence.\n\n"

                        "Use search_live_project only when the "
                        "AnalysisOutput does not contain enough "
                        "current-project detail to construct or "
                        "evaluate a strategy.\n\n"

                        "Use simulate_strategy to evaluate every "
                        "strategy that you intend to compare or "
                        "select.\n\n"

                        "Never invent simulation results. "
                        "All BEFORE, AFTER, comparison, affected "
                        "tasks, and modified tasks information "
                        "must come from simulate_strategy.\n\n"

                        "Do not invent productivity, resource "
                        "capacity, hiring time, onboarding time, "
                        "cost, completion dates, days saved, or "
                        "delay reduction unless they are explicitly "
                        "supported by the simulator output.\n\n"

                        "If expected delay reduction cannot be "
                        "calculated reliably, set it to null and "
                        "explain the limitation in warnings.\n"
                    )
                }
            )

            raw_output = result["output"]

            return self._validate_output(
                raw_output
            )

    def _validate_output(
        self,
        raw_output: str,
    ) -> dict:
        """
        Validate the final SimulationOutput.
        """

        if not raw_output:
            raise ValueError(
                "Simulation Agent returned an empty output."
            )

        cleaned_output = raw_output.strip()

        if cleaned_output.startswith(
            "```json"
        ):
            cleaned_output = cleaned_output[7:]

        elif cleaned_output.startswith(
            "```"
        ):
            cleaned_output = cleaned_output[3:]

        if cleaned_output.endswith(
            "```"
        ):
            cleaned_output = (
                cleaned_output[:-3]
            )

        cleaned_output = cleaned_output.strip()

        simulation = (
            SimulationOutput.model_validate_json(
                cleaned_output
            )
        )

        return simulation.model_dump()