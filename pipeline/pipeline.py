
"""
UnderControl Analysis Pipeline

Flow:
    User CSV
        -> SchemaMapper
        -> Standardized DataFrame

    Standardized DataFrame
        -> ProjectAnalyzer
        -> Project Metrics

    Standardized DataFrame
        -> Live RAG
        -> Live RAG Tool

    Ground Truth RAG
        -> Ground Truth Retriever
        -> Ground Truth Tool

    Project Metrics
    + Live RAG
    + Ground Truth RAG
        -> Analysis Agent
        -> AnalysisOutput

    AnalysisOutput
    + Live RAG
    + Project Data
        -> Simulation Agent
        -> SimulationOutput

    Final Result:
        {
            "analysis": AnalysisOutput,
            "simulation": SimulationOutput,
            "project_dataframe": DataFrame
        }
"""

import pandas as pd

from preprocessing.schema_mapper import SchemaMapper
from analysis.project_analyzer import ProjectAnalyzer

from rag.build_rag import build_live_rag
from rag.retriever import (
    GroundTruthRetriever,
    build_live_rag_tool,
    build_ground_truth_rag_tool,
)

from agents.analysis_agent import (
    AnalysisAgent,
    build_analysis_tools,
)

from agents.simulation_agent import (
    SimulationAgent,
    build_simulation_tools,
)

from prompts.analysis_prompt import analysis_prompt
from prompts.simulation_prompt import simulation_prompt

from llm.model import create_agent_llm


def run_analysis(user_df):
    """
    Run the complete UnderControl pipeline.

    Args:
        user_df: Input project data as a pandas DataFrame.

    Returns:
        dict containing:
            - analysis
            - simulation
            - project_dataframe

    Raises:
        TypeError: If the input is not a pandas DataFrame.
        ValueError: If the input DataFrame is empty.
    """

    # =====================================================
    # 0. Validate input data
    # =====================================================

    if not isinstance(user_df, pd.DataFrame):
        raise TypeError(
            "Input data must be a pandas DataFrame."
        )

    if user_df.empty:
        raise ValueError(
            "Input data is empty. Please upload a CSV file with data."
        )

    # =====================================================
    # 1. Standardize uploaded data
    # =====================================================

    mapping_result = SchemaMapper().map_schema(
        user_df
    )

    standardized_df = mapping_result["dataframe"]

    # =====================================================
    # 2. Prepare project data and calculate metrics
    # =====================================================

    analyzer = ProjectAnalyzer()

    prepared_project = analyzer.prepare_project(
        standardized_df
    )

    project_df = prepared_project["dataframe"]
    project_metrics = prepared_project["metrics"]

    # =====================================================
    # 3. Build Live RAG
    # =====================================================

    live_collection = build_live_rag(
        project_df
    )

    live_rag_tool = build_live_rag_tool(
        live_collection
    )

    # =====================================================
    # 4. Connect Ground Truth RAG
    # =====================================================

    ground_truth_retriever = GroundTruthRetriever()

    ground_truth_rag_tool = build_ground_truth_rag_tool(
        ground_truth_retriever
    )

    # =====================================================
    # 5. Create shared LLM
    # =====================================================

    llm = create_agent_llm()

    # =====================================================
    # 6. Build Analysis Agent tools
    # =====================================================

    analysis_tools = build_analysis_tools(
        project_metrics=project_metrics,
        live_rag_tool=live_rag_tool,
        ground_truth_rag_tool=ground_truth_rag_tool,
    )

    # =====================================================
    # 7. Run Analysis Agent
    # =====================================================

    analysis_agent = AnalysisAgent(
        llm=llm,
        prompt=analysis_prompt,
        tools=analysis_tools,
        verbose=False,
    )

    analysis_result = analysis_agent.analyze()

    # =====================================================
    # 8. Build Simulation Agent tools
    # =====================================================

    simulation_tools = build_simulation_tools(
        project_df=project_df,
        live_rag_tool=live_rag_tool,
    )

    # =====================================================
    # 9. Run Simulation Agent
    # =====================================================

    simulation_agent = SimulationAgent(
        llm=llm,
        prompt=simulation_prompt,
        tools=simulation_tools,
        analysis_output=analysis_result,
        verbose=False,
    )

    simulation_result = simulation_agent.simulate()

    # =====================================================
    # 10. Return complete pipeline result
    # =====================================================

    return {
        "analysis": analysis_result,
        "simulation": simulation_result,
        "project_dataframe": project_df,
    }