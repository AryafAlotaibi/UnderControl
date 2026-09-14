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
    + Live RAG Retriever
    + Ground Truth Retriever
        -> Analysis Agent
        -> AnalysisOutput
"""

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

from prompts.analysis_prompt import analysis_prompt
from llm.model import create_agent_llm


def run_analysis(user_df):

    # 1. Standardize uploaded data
    mapping_result = SchemaMapper().map_schema(user_df)

    standardized_df = mapping_result["dataframe"]

    # 2. Prepare data + calculate deterministic metrics
    analyzer = ProjectAnalyzer()

    prepared_project = analyzer.prepare_project(
        standardized_df
    )

    project_df = prepared_project["dataframe"]
    project_metrics = prepared_project["metrics"]

    # 3. Build temporary Live RAG
    live_collection = build_live_rag(
        project_df
    )

    live_rag_tool = build_live_rag_tool(
        live_collection
    )

    # 4. Connect persistent Ground Truth RAG
    ground_truth_retriever = GroundTruthRetriever()

    ground_truth_rag_tool = build_ground_truth_rag_tool(
        ground_truth_retriever
    )

    # 5. Give all tools to the Analysis Agent
    tools = build_analysis_tools(
        project_metrics=project_metrics,
        live_rag_tool=live_rag_tool,
        ground_truth_rag_tool=ground_truth_rag_tool,
    )

    # 6. Create and run Analysis Agent
    agent = AnalysisAgent(
        llm=create_agent_llm(),
        prompt=analysis_prompt,
        tools=tools,
        verbose=True,
    )

    return agent.analyze()