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
    Generate, simulate, compare, and select recovery actions.

    The Analysis Agent provides the diagnosis. A small deterministic
    fallback candidate rule guarantees that an obvious evidence-based
    management action is actually tested instead of being rejected
    before simulation.
    """

    PRIORITY_RANK = {
        "lowest": 0,
        "low": 1,
        "medium": 2,
        "normal": 2,
        "high": 3,
        "highest": 4,
        "critical": 5,
    }

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
            max_iterations=4,
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
                query = "current project bottlenecks and blocked tasks"

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
    # Deterministic Candidate Generation
    # =====================================================

    def _build_required_candidates(self):
        """
        Build conservative fallback candidates for every blocked
        bottleneck that is below the highest observed project priority.

        These candidates are only testable management actions.
        They are not automatic recommendations.
        """

        if self.analysis_output.project_state != "delayed":
            return []

        bottlenecks = self.analysis_output.model_dump().get(
            "bottlenecks",
            [],
        )

        observed_priorities = []

        for item in bottlenecks:
            priority = item.get("priority")

            if not priority:
                continue

            normalized = str(priority).strip().lower()

            if normalized in self.PRIORITY_RANK:
                observed_priorities.append(
                    str(priority).strip()
                )

        if not observed_priorities:
            return []

        highest_priority = max(
            observed_priorities,
            key=lambda value: self.PRIORITY_RANK[
                value.lower()
            ],
        )

        highest_rank = self.PRIORITY_RANK[
            highest_priority.lower()
        ]

        candidates = []

        for item in bottlenecks:
            task_id = item.get("task_id")
            status = item.get("status")
            priority = item.get("priority")

            if not task_id or not priority:
                continue

            current_rank = self.PRIORITY_RANK.get(
                str(priority).strip().lower()
            )

            if current_rank is None:
                continue

            is_blocked = (
                str(status).strip().lower()
                == "blocked"
            )

            if (
                is_blocked
                and current_rank < highest_rank
            ):
                candidate = {
                    "type": "reprioritization",
                    "description": (
                        f"Raise blocked bottleneck {task_id} "
                        f"from {priority} to {highest_priority} "
                        "and test whether supported project "
                        "signals improve."
                    ),
                    "target_tasks": [
                        str(task_id).strip()
                    ],
                    "changes": {
                        "priority": {
                            "to": highest_priority
                        }
                    },
                }

                candidates.append(candidate)

        return candidates

    def _simulate_required_candidates(
        self,
        candidates,
    ):
        """
        Run deterministic fallback candidates before the LLM evaluates
        them. This guarantees that a valid fallback candidate is truly
        simulated rather than rejected before testing.
        """

        if not candidates:
            return []

        simulation_tool = self._get_tool(
            "simulate_strategy"
        )

        if simulation_tool is None:
            raise RuntimeError(
                "simulate_strategy tool is not available."
            )

        results = []

        for candidate in candidates:
            strategy_json = json.dumps(
                candidate,
                ensure_ascii=False,
            )

            raw_result = simulation_tool.invoke(
                {"strategy": strategy_json}
            )

            if isinstance(raw_result, str):
                parsed_result = json.loads(raw_result)
            elif isinstance(raw_result, dict):
                parsed_result = raw_result
            else:
                raise TypeError(
                    "simulate_strategy returned an unsupported result."
                )

            results.append(parsed_result)

        return results

    # =====================================================
    # Main Agent Run
    # =====================================================

    def simulate(self) -> dict:
        """Generate and evaluate recovery strategies."""

        analysis_json = self.analysis_output.model_dump_json(
            indent=2
        )

        live_context = self._get_live_project_context()

        required_candidates = (
            self._build_required_candidates()
        )

        required_results = (
            self._simulate_required_candidates(
                required_candidates
            )
        )

        required_candidates_json = json.dumps(
            required_candidates,
            indent=2,
            ensure_ascii=False,
        )

        required_results_json = json.dumps(
            required_results,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        result = self.executor.invoke(
            {
                "input": (
                    "Use the AnalysisOutput as the starting diagnosis.\n\n"
                    "AnalysisOutput:\n"
                    f"{analysis_json}\n\n"
                    "Live Project Context:\n"
                    f"{live_context}\n\n"
                    "Required Candidate Strategies:\n"
                    f"{required_candidates_json}\n\n"
                    "Required Simulation Results:\n"
                    f"{required_results_json}\n\n"
                    "Required Candidate Strategies were generated by "
                    "a deterministic candidate rule. They are not "
                    "recommendations. They only represent management "
                    "actions that are reasonable enough to test.\n\n"
                    "Required Simulation Results were already produced "
                    "by simulate_strategy before this LLM evaluation. "
                    "Preserve these results exactly.\n\n"
                    "If Required Candidate Strategies is not empty, "
                    "include every required candidate in "
                    "candidate_strategies and every required result in "
                    "simulated_strategies. Do not reject a required "
                    "candidate before evaluation.\n\n"
                    "If Required Simulation Results is not empty, do not "
                    "generate additional simulation candidates and do not "
                    "call tools again. Evaluate the supplied results and "
                    "produce the final recovery guidance. If Required "
                    "Simulation Results is empty, an additional evidence-"
                    "supported candidate may be created, but it must be "
                    "simulated before appearing in the final answer.\n\n"
                    "Judge effectiveness only from actual simulator "
                    "before/after/comparison values. A feasible strategy "
                    "does not have to be selected.\n\n"
                    "Never invent delay reduction, productivity, resource "
                    "capacity, cost, completion dates, or days saved."
                )
            }
        )

        output = self._validate_output(
            result.get("output")
        )

        return self._enforce_required_results(
            output=output,
            required_candidates=required_candidates,
            required_results=required_results,
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

    # =====================================================
    # Required Result Safety Net
    # =====================================================

    @staticmethod
    def _strategy_key(strategy):
        return json.dumps(
            {
                "type": strategy.get("type"),
                "target_tasks": strategy.get(
                    "target_tasks",
                    [],
                ),
                "changes": strategy.get(
                    "changes",
                    {},
                ),
            },
            sort_keys=True,
            ensure_ascii=False,
        )

    def _build_comparison_from_result(self, result):
        """Create a conservative text comparison from simulator facts."""

        strategy = result.get("strategy") or {}
        comparison = result.get("comparison") or {}
        schedule = comparison.get("schedule_signals") or {}

        improvements = []
        unchanged = []

        for metric_name, values in schedule.items():
            delta = values.get("delta")

            if delta is None:
                continue

            if delta < 0:
                improvements.append(
                    f"{metric_name} decreased by {abs(delta)}"
                )
            elif delta == 0:
                unchanged.append(metric_name)

        if improvements:
            effectiveness = (
                "Supported improvement: "
                + "; ".join(improvements)
                + "."
            )
        elif unchanged:
            effectiveness = (
                "No improvement was demonstrated in the supported "
                "schedule signals."
            )
        else:
            effectiveness = (
                "The simulator applied the change, but the available "
                "comparison does not establish a schedule improvement."
            )

        return {
            "strategy_type": strategy.get(
                "type",
                "unknown",
            ),
            "effectiveness": effectiveness,
            "feasibility": result.get(
                "status",
                "unknown",
            ),
            "risk": result.get(
                "risk",
                "unknown",
            ),
            "resource_impact": result.get(
                "resource_impact",
                "unknown",
            ),
            "summary": (
                "This candidate was simulated using the deterministic "
                "project simulator and evaluated from its actual "
                "before/after metrics."
            ),
        }

    def _enforce_required_results(
        self,
        output,
        required_candidates,
        required_results,
    ):
        """
        Safety net: if the LLM omits a deterministic required candidate
        or its real simulator result, restore those factual values.
        """

        if not required_candidates:
            return output

        candidate_keys = {
            self._strategy_key(item)
            for item in output.get(
                "candidate_strategies",
                [],
            )
        }

        for candidate in required_candidates:
            key = self._strategy_key(candidate)

            if key not in candidate_keys:
                output.setdefault(
                    "candidate_strategies",
                    [],
                ).append(candidate)
                candidate_keys.add(key)

        simulated_keys = {
            self._strategy_key(
                item.get("strategy") or {}
            )
            for item in output.get(
                "simulated_strategies",
                [],
            )
        }

        added_result = False

        for simulation_result in required_results:
            strategy = simulation_result.get(
                "strategy"
            ) or {}
            key = self._strategy_key(strategy)

            if key not in simulated_keys:
                output.setdefault(
                    "simulated_strategies",
                    [],
                ).append(simulation_result)
                simulated_keys.add(key)
                added_result = True

        if added_result and not output.get("comparison"):
            output["comparison"] = [
                self._build_comparison_from_result(
                    simulation_result
                )
                for simulation_result in required_results
            ]

        if added_result:
            output["explanation"] = (
                "At least one evidence-based management candidate was "
                "tested with the deterministic simulator. The strategy "
                "is selected only if the actual before/after metrics "
                "show a meaningful supported improvement."
            )

            contradictory_phrases = (
                "no simulator call",
                "no simulator calls",
                "no supported recovery strategy was simulated",
                "no candidate strategy was created",
                "no candidates were advanced",
            )

            cleaned_warnings = []

            for warning in output.get("warnings") or []:
                normalized = str(warning).lower()

                if any(
                    phrase in normalized
                    for phrase in contradictory_phrases
                ):
                    continue

                cleaned_warnings.append(warning)

            output["warnings"] = cleaned_warnings

        assumption = (
            "Deterministic fallback candidates are testable management "
            "actions, not automatic recommendations."
        )

        assumptions = output.setdefault(
            "assumptions",
            [],
        )

        if assumption not in assumptions:
            assumptions.append(assumption)

        validated = SimulationOutput.model_validate(
            output
        )

        return validated.model_dump()
