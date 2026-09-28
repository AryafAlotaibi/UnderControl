import pandas as pd
import pytest

from analysis.project_analyzer import ProjectAnalyzer


def test_input_must_be_dataframe():
    analyzer = ProjectAnalyzer()

    with pytest.raises(
        TypeError,
        match="df must be a pandas DataFrame",
    ):
        analyzer.prepare_project([{"status": "Open"}])


def test_empty_dataframe_returns_zero_issues():
    analyzer = ProjectAnalyzer()
    df = pd.DataFrame()

    result = analyzer.prepare_project(df)

    assert result["metrics"]["total_issues"] == 0


def test_invalid_dates_are_converted_to_nat():
    analyzer = ProjectAnalyzer()
    df = pd.DataFrame({
        "due_date": ["not-a-date"],
    })

    result = analyzer.prepare_project(df)

    assert pd.isna(result["dataframe"]["due_date"].iloc[0])


def test_invalid_numeric_values_are_converted_to_nan():
    analyzer = ProjectAnalyzer()
    df = pd.DataFrame({
        "story_point": ["not-a-number"],
    })

    result = analyzer.prepare_project(df)

    assert pd.isna(result["dataframe"]["story_point"].iloc[0])


def test_missing_columns_do_not_raise_error():
    analyzer = ProjectAnalyzer()
    df = pd.DataFrame({
        "unrelated_column": ["value"],
    })

    result = analyzer.prepare_project(df)

    assert result["metrics"]["total_issues"] == 1
    assert result["metrics"]["status_distribution"] == {}