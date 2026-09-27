import pandas as pd
import pytest

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