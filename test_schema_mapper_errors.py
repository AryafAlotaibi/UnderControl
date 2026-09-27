
import httpx
import pandas as pd
import pytest

from unittest.mock import MagicMock

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)

from preprocessing.schema_mapper import SchemaMapper


@pytest.fixture
def sample_df():
    """Create a small DataFrame for testing."""
    return pd.DataFrame({
        "ticket_id": ["TASK-1", "TASK-2"],
        "status": ["Open", "Done"],
    })


def test_schema_mapper_handles_connection_error(sample_df):
    """Return a clear error when the LLM connection fails."""
    fake_client = MagicMock()

    fake_client.chat.completions.create.side_effect = (
        APIConnectionError(
            message="Connection failed",
            request=httpx.Request(
                "POST",
                "https://example.com",
            ),
        )
    )

    mapper = SchemaMapper(llm_client=fake_client)

    with pytest.raises(
        RuntimeError,
        match="could not connect to the LLM service",
    ) as error:
        mapper.map_schema(sample_df)

    assert isinstance(error.value.__cause__, APIConnectionError)


def test_schema_mapper_handles_timeout(sample_df):
    """Return a clear error when the LLM request times out."""
    fake_client = MagicMock()

    fake_client.chat.completions.create.side_effect = (
        APITimeoutError(
            request=httpx.Request(
                "POST",
                "https://example.com",
            ),
        )
    )

    mapper = SchemaMapper(llm_client=fake_client)

    with pytest.raises(
        RuntimeError,
        match="LLM request timed out",
    ) as error:
        mapper.map_schema(sample_df)

    assert isinstance(error.value.__cause__, APITimeoutError)


def test_schema_mapper_handles_api_status_error(sample_df):
    """Return a clear error when the LLM service returns an HTTP error."""
    fake_client = MagicMock()

    request = httpx.Request(
        "POST",
        "https://example.com",
    )

    response = httpx.Response(
        status_code=500,
        request=request,
    )

    fake_client.chat.completions.create.side_effect = (
        APIStatusError(
            message="Internal server error",
            response=response,
            body=None,
        )
    )

    mapper = SchemaMapper(llm_client=fake_client)

    with pytest.raises(
        RuntimeError,
        match="HTTP status 500",
    ) as error:
        mapper.map_schema(sample_df)

    assert isinstance(error.value.__cause__, APIStatusError)