
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