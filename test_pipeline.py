
import pandas as pd
import pytest
from unittest.mock import patch

from pipeline.pipeline import run_analysis


def test_input_must_be_dataframe():
    """Reject inputs that are not pandas DataFrames."""

    with pytest.raises(
        TypeError,
        match="Input data must be a pandas DataFrame.",
    ):
        run_analysis(None)


def test_input_dataframe_must_not_be_empty():
    """Reject an empty DataFrame."""

    empty_df = pd.DataFrame()

    with pytest.raises(
        ValueError,
        match="Input data is empty.",
    ):
        run_analysis(empty_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
def test_csv_without_task_information_is_rejected(mock_map_schema):
    """Reject files without recognizable task information."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": [None],
            "issue_key": [None],
            "text": [None],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    user_df = pd.DataFrame({
        "Name": ["Lana"],
        "City": ["Riyadh"],
        "Country": ["Saudi Arabia"],
    })

    with pytest.raises(
        ValueError,
        match="doesn't contain enough task information",
    ):
        run_analysis(user_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
def test_csv_with_task_description_passes_validation(mock_map_schema):
    """Verify that task descriptions pass the validation."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": [None],
            "issue_key": [None],
            "text": ["Fix login issue"],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    user_df = pd.DataFrame({
        "Task Description": ["Fix login issue"],
    })

    with patch(
        "pipeline.pipeline.ProjectAnalyzer.prepare_project",
        side_effect=RuntimeError("Validation passed"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Validation passed",
        ):
            run_analysis(user_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
@patch("pipeline.pipeline.build_live_rag")
def test_live_rag_error_propagates(
    mock_build_live_rag,
    mock_map_schema,
):
    """Verify that Live RAG errors propagate to the caller."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": ["TASK-1"],
            "issue_key": ["TASK-1"],
            "text": ["Fix login issue"],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    mock_build_live_rag.side_effect = RuntimeError(
        "Live RAG connection failed"
    )

    user_df = pd.DataFrame({
        "Task Description": ["Fix login issue"],
    })

    with pytest.raises(
        RuntimeError,
        match="Live RAG connection failed",
    ):
        run_analysis(user_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
@patch("pipeline.pipeline.build_live_rag")
@patch("pipeline.pipeline.GroundTruthRetriever")
def test_ground_truth_rag_error_propagates(
    mock_ground_truth_retriever,
    mock_build_live_rag,
    mock_map_schema,
):
    """Verify that Ground Truth RAG errors propagate to the caller."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": ["TASK-1"],
            "issue_key": ["TASK-1"],
            "text": ["Fix login issue"],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    mock_build_live_rag.return_value = object()

    mock_ground_truth_retriever.side_effect = RuntimeError(
        "Ground Truth RAG initialization failed"
    )

    user_df = pd.DataFrame({
        "Task Description": ["Fix login issue"],
    })

    with pytest.raises(
        RuntimeError,
        match="Ground Truth RAG initialization failed",
    ):
        run_analysis(user_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
@patch("pipeline.pipeline.build_live_rag")
@patch("pipeline.pipeline.GroundTruthRetriever")
@patch("pipeline.pipeline.create_agent_llm")
@patch("pipeline.pipeline.AnalysisAgent")
def test_analysis_agent_error_propagates(
    mock_analysis_agent,
    mock_create_llm,
    mock_ground_truth_retriever,
    mock_build_live_rag,
    mock_map_schema,
):
    """Verify that Analysis Agent errors propagate to the caller."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": ["TASK-1"],
            "issue_key": ["TASK-1"],
            "text": ["Fix login issue"],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    mock_build_live_rag.return_value = object()
    mock_ground_truth_retriever.return_value = object()
    mock_create_llm.return_value = object()

    mock_analysis_agent.return_value.analyze.side_effect = RuntimeError(
        "Analysis Agent execution failed"
    )

    user_df = pd.DataFrame({
        "Task Description": ["Fix login issue"],
    })

    with pytest.raises(
        RuntimeError,
        match="Analysis Agent execution failed",
    ):
        run_analysis(user_df)


@patch("pipeline.pipeline.SchemaMapper.map_schema")
@patch("pipeline.pipeline.build_live_rag")
@patch("pipeline.pipeline.GroundTruthRetriever")
@patch("pipeline.pipeline.create_agent_llm")
@patch("pipeline.pipeline.AnalysisAgent")
@patch("pipeline.pipeline.SimulationAgent")
def test_simulation_agent_error_propagates(
    mock_simulation_agent,
    mock_analysis_agent,
    mock_create_llm,
    mock_ground_truth_retriever,
    mock_build_live_rag,
    mock_map_schema,
):
    """Verify that Simulation Agent errors propagate to the caller."""

    mock_map_schema.return_value = {
        "dataframe": pd.DataFrame({
            "issue_id": ["TASK-1"],
            "issue_key": ["TASK-1"],
            "text": ["Fix login issue"],
            "status": ["Open"],
            "priority": ["High"],
        })
    }

    mock_build_live_rag.return_value = object()
    mock_ground_truth_retriever.return_value = object()
    mock_create_llm.return_value = object()

    # Allow the Analysis Agent to complete successfully.
    mock_analysis_agent.return_value.analyze.return_value = (
        "Analysis completed"
    )

    # Simulate an error during simulation.
    mock_simulation_agent.return_value.simulate.side_effect = RuntimeError(
        "Simulation Agent execution failed"
    )

    user_df = pd.DataFrame({
        "Task Description": ["Fix login issue"],
    })

    with pytest.raises(
        RuntimeError,
        match="Simulation Agent execution failed",
    ):
        run_analysis(user_df)