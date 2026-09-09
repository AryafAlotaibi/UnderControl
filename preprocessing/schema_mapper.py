import json

from llm.model import client, SCHEMA_MODEL
from prompts.schema_mapping_prompt import build_schema_mapping_prompt


class SchemaMapper:

    # The standard schema used internally by UnderControl
    STANDARD_SCHEMA = {
        "issue_id": "Unique identifier for the issue or task",

        "project_key": "Unique project identifier or key",

        "project_name": "Name of the project",

        "issue_key": "Readable issue or ticket key",

        "type": "Type or category of the issue or task",

        "priority": "Priority or severity level",

        "status": "Current workflow status of the issue or task",

        "resolution": "Final resolution or outcome of the issue",

        "creation_date": "Date and time when the issue was created",

        "resolution_date": (
            "Date and time when the issue was resolved or completed"
        ),

        "story_point": "Estimated effort expressed in story points",

        "resolution_time_minutes": (
            "Total time required to resolve the issue in minutes"
        ),

        "in_progress_minutes": (
            "Time the issue spent in progress in minutes"
        ),

        "assignee_id": (
            "Identifier of the person responsible for the issue"
        ),

        "text": (
            "Issue title, description, summary, or textual content"
        ),

        "dependency": (
            "Dependency, blocking, or linked-issue relationship"
        )
    }


    def __init__(self, llm_client=None, model=SCHEMA_MODEL):
        """
        Use GPT-5.6 Luna by default.
        A different client or model can be provided later if needed.
        """

        self.client = llm_client or client
        self.model = model


    def get_column_samples(self, df, sample_size=3):
        """
        Get a few sample values from every user column.

        The LLM uses both:
        1. Column name
        2. Sample values

        to understand the meaning of each column.
        """

        samples = {}

        for column in df.columns:

            values = (
                df[column]
                .dropna()
                .astype(str)
                .head(sample_size)
                .tolist()
            )

            samples[column] = values

        return samples


    def get_schema_info(self, df):
        """
        Prepare the information that will be sent
        to the LLM for semantic schema matching.
        """

        return {
            "user_columns": list(df.columns),

            "column_samples": self.get_column_samples(df),

            "standard_schema": self.STANDARD_SCHEMA
        }


    def validate_mapping(self, df, mapping, confidence):
        """
        Validate the mapping returned by the LLM.

        Prevent:
        - Mapping columns that do not exist
        - Mapping to an unknown standard feature
        - Mapping multiple user columns to the same standard feature

        If two columns map to the same standard feature,
        keep the mapping with the higher confidence.
        """

        valid_mapping = {}

        used_standard_columns = {}

        for user_column, standard_column in mapping.items():

            if user_column not in df.columns:
                continue

            if standard_column not in self.STANDARD_SCHEMA:
                continue

            current_confidence = float(
                confidence.get(user_column, 0.0)
            )

            # First column mapped to this standard feature
            if standard_column not in used_standard_columns:

                valid_mapping[user_column] = standard_column

                used_standard_columns[standard_column] = {
                    "user_column": user_column,
                    "confidence": current_confidence
                }

            else:

                existing = used_standard_columns[standard_column]

                # Keep the mapping with higher confidence
                if current_confidence > existing["confidence"]:

                    old_user_column = existing["user_column"]

                    valid_mapping.pop(
                        old_user_column,
                        None
                    )

                    valid_mapping[user_column] = standard_column

                    used_standard_columns[standard_column] = {
                        "user_column": user_column,
                        "confidence": current_confidence
                    }

        return valid_mapping


    def apply_mapping(self, df, mapping):
        """
        Rename the user's columns into UnderControl's
        standard column names.
        """

        return df.rename(columns=mapping).copy()


    def get_missing_columns(self, mapped_df):
        """
        Find standard UnderControl features
        that do not exist in the uploaded CSV.
        """

        return [
            column
            for column in self.STANDARD_SCHEMA
            if column not in mapped_df.columns
        ]


    def get_unmapped_columns(self, original_df, mapping):
        """
        Find uploaded columns that were not matched
        with any UnderControl feature.
        """

        return [
            column
            for column in original_df.columns
            if column not in mapping
        ]


    def map_schema(self, df):
        """
        Main schema mapping workflow.

        User CSV
            ↓
        Column names + sample values
            ↓
        GPT-5.6 Luna
            ↓
        Semantic column mapping
            ↓
        Python validation
            ↓
        Standardized DataFrame
        """

        # Prepare user schema information
        schema_info = self.get_schema_info(df)

        # Build the schema mapping prompt
        prompt = build_schema_mapping_prompt(
            standard_schema=self.STANDARD_SCHEMA,
            user_columns=schema_info["user_columns"],
            column_samples=schema_info["column_samples"]
        )

        # Ask GPT-5.6 Luna to understand and map the columns
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={
                "effort": "low"
            },
            text={
                "format": {
                    "type": "json_object"
                }
            }
        )

        # Convert LLM JSON response into Python dictionary
        result = json.loads(response.output_text)

        raw_mapping = result.get(
            "mapping",
            {}
        )

        raw_confidence = result.get(
            "confidence",
            {}
        )

        # Validate the LLM mapping using Python
        valid_mapping = self.validate_mapping(
            df,
            raw_mapping,
            raw_confidence
        )

        # Keep confidence only for accepted mappings
        valid_confidence = {
            column: raw_confidence.get(column, 0.0)
            for column in valid_mapping
        }

        # Rename columns
        mapped_df = self.apply_mapping(
            df,
            valid_mapping
        )

        # Calculate these ourselves instead of trusting the LLM
        missing_columns = self.get_missing_columns(
            mapped_df
        )

        unmapped_columns = self.get_unmapped_columns(
            df,
            valid_mapping
        )

        return {
            "dataframe": mapped_df,

            "mapping": valid_mapping,

            "confidence": valid_confidence,

            "unmapped_columns": unmapped_columns,

            "missing_columns": missing_columns
        }