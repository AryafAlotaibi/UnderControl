import json
import pandas as pd

from llm.model import client, SCHEMA_MODEL
from prompts.schema_mapping_prompt import build_schema_mapping_prompt


class SchemaMapper:

    STANDARD_SCHEMA = {
        "issue_id": (
            "Internal unique identifier for an issue or task"
        ),

        "project_key": (
            "Short unique identifier or key for the project"
        ),

        "project_name": (
            "Human-readable name of the project"
        ),

        "issue_key": (
            "Human-readable issue, ticket, or task key"
        ),

        "type": (
            "Type or category of the issue or task"
        ),

        "priority": (
            "Priority, severity, or importance level of the issue or task"
        ),

        "status": (
            "Current workflow state or status of the issue or task"
        ),

        "resolution": (
            "Final resolution, outcome, or closure result of the issue"
        ),

        "creation_date": (
            "Date and time when the issue or task was created"
        ),

        "due_date": (
            "Planned deadline or due date for the issue or task"
        ),

        "resolution_date": (
            "Actual date and time when the issue or task was resolved "
            "or completed"
        ),

        "story_point": (
            "Estimated effort or complexity expressed as story points"
        ),

        "resolution_time_minutes": (
            "Total elapsed time required to resolve the issue, in minutes"
        ),

        "in_progress_minutes": (
            "Time spent actively in the in-progress state, in minutes"
        ),

        "assignee_id": (
            "Identifier of the person responsible for the issue or task"
        ),

        "text": (
            "Useful textual content describing the issue or task. "
            "Multiple source columns may contribute to this field."
        ),

        "dependency": (
            "Dependency-related information showing prerequisites, "
            "blocking relationships, linked tasks, or dependent issues. "
            "Multiple source columns may contribute to this field."
        )
    }

    # These fields intentionally allow many source columns
    MULTI_SOURCE_FIELDS = {
        "text",
        "dependency"
    }


    def __init__(self, llm_client=None, model=SCHEMA_MODEL):
        self.client = llm_client or client
        self.model = model


    def get_column_samples(self, df, sample_size=3):
        """
        Collect a few non-empty sample values from each uploaded column.

        The LLM uses the samples together with the column name
        to understand the semantic meaning of the field.
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
        Prepare schema information that will be sent to the LLM.
        """

        return {
            "user_columns": list(df.columns),
            "column_samples": self.get_column_samples(df),
            "standard_schema": self.STANDARD_SCHEMA
        }


    def validate_mapping(self, df, mapping, confidence):
        """
        Validate the semantic mapping proposed by the LLM.

        Rules:
        - Source columns must exist in the uploaded DataFrame.
        - Target fields must exist in STANDARD_SCHEMA.
        - Normal standard fields are one-to-one.
        - text and dependency support many-to-one mapping.
        - If multiple columns compete for a normal standard field,
          keep the mapping with the higher LLM confidence.
        """

        valid_mapping = {}
        used_standard_fields = {}

        for user_column, standard_field in mapping.items():

            if user_column not in df.columns:
                continue

            if standard_field not in self.STANDARD_SCHEMA:
                continue

            current_confidence = float(
                confidence.get(user_column, 0.0)
            )

            # text and dependency intentionally support many-to-one
            if standard_field in self.MULTI_SOURCE_FIELDS:
                valid_mapping[user_column] = standard_field
                continue

            # First mapping to this standard field
            if standard_field not in used_standard_fields:

                valid_mapping[user_column] = standard_field

                used_standard_fields[standard_field] = {
                    "user_column": user_column,
                    "confidence": current_confidence
                }

                continue

            # Another source column was mapped to the same standard field
            existing = used_standard_fields[standard_field]

            if current_confidence > existing["confidence"]:

                previous_column = existing["user_column"]

                valid_mapping.pop(
                    previous_column,
                    None
                )

                valid_mapping[user_column] = standard_field

                used_standard_fields[standard_field] = {
                    "user_column": user_column,
                    "confidence": current_confidence
                }

        return valid_mapping


    @staticmethod
    def _has_value(value):
        """
        Check whether a cell contains useful information.
        """

        if value is None:
            return False

        try:
            if pd.isna(value):
                return False
        except (TypeError, ValueError):
            pass

        text = str(value).strip()

        return bool(text) and text.lower() != "nan"


    def merge_source_columns(self, df, source_columns, target_field):
        """
        Merge several semantically related source columns into one
        standardized field.

        The original source-column labels are preserved in the value
        so information such as dependency direction is not lost.

        Example:

        Summary: API integration issue
        Description: Authentication request fails

        or:

        blocked_by: TASK-10
        blocks: TASK-24
        """

        if not source_columns:
            return df

        df = df.copy()

        def combine_row(row):
            parts = []

            for source_column in source_columns:

                value = row[source_column]

                if self._has_value(value):
                    parts.append(
                        f"{source_column}: {str(value).strip()}"
                    )

            return "\n".join(parts)

        df[target_field] = df.apply(
            combine_row,
            axis=1
        )

        # Source columns have now been consolidated into target_field
        columns_to_drop = [
            column
            for column in source_columns
            if column != target_field
        ]

        df = df.drop(
            columns=columns_to_drop,
            errors="ignore"
        )

        return df


    def apply_mapping(self, df, mapping):
        """
        Apply the validated mapping to the uploaded DataFrame.

        Normal fields:
            renamed directly.

        text and dependency:
            multiple source columns are merged into one standard field.

        Columns that are not mapped are intentionally preserved.
        """

        mapped_df = df.copy()

        multi_source_mapping = {
            field: []
            for field in self.MULTI_SOURCE_FIELDS
        }

        normal_mapping = {}

        for user_column, standard_field in mapping.items():

            if standard_field in self.MULTI_SOURCE_FIELDS:
                multi_source_mapping[standard_field].append(
                    user_column
                )

            else:
                normal_mapping[user_column] = standard_field

        # Rename one-to-one fields
        mapped_df = mapped_df.rename(
            columns=normal_mapping
        )

        # Merge many-to-one fields
        for target_field, source_columns in multi_source_mapping.items():

            if source_columns:
                mapped_df = self.merge_source_columns(
                    mapped_df,
                    source_columns,
                    target_field
                )

        return mapped_df


    def get_missing_columns(self, mapped_df):
        """
        Return standard UnderControl fields that were not found
        in the uploaded dataset.
        """

        return [
            field
            for field in self.STANDARD_SCHEMA
            if field not in mapped_df.columns
        ]


    def get_unmapped_columns(self, original_df, mapping):
        """
        Return uploaded columns that did not map to the standard schema.

        Important:
        These columns are NOT deleted.
        They remain available in the standardized DataFrame.
        """

        return [
            column
            for column in original_df.columns
            if column not in mapping
        ]


    def map_schema(self, df):
        """
        Main schema-mapping workflow.

        User DataFrame
            ↓
        Column names + sample values
            ↓
        GPT-5.6 Luna semantic matching
            ↓
        Python validation
            ↓
        Rename / merge mapped fields
            ↓
        Standardized DataFrame
        """

        schema_info = self.get_schema_info(df)

        prompt = build_schema_mapping_prompt(
            standard_schema=self.STANDARD_SCHEMA,
            user_columns=schema_info["user_columns"],
            column_samples=schema_info["column_samples"]
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_object"
            }
        )

        result = json.loads(
            response.choices[0].message.content
        )

        raw_mapping = result.get(
            "mapping",
            {}
        )

        raw_confidence = result.get(
            "confidence",
            {}
        )

        valid_mapping = self.validate_mapping(
            df=df,
            mapping=raw_mapping,
            confidence=raw_confidence
        )

        valid_confidence = {
            column: float(
                raw_confidence.get(column, 0.0)
            )
            for column in valid_mapping
        }

        mapped_df = self.apply_mapping(
            df=df,
            mapping=valid_mapping
        )

        missing_columns = self.get_missing_columns(
            mapped_df
        )

        unmapped_columns = self.get_unmapped_columns(
            original_df=df,
            mapping=valid_mapping
        )

        return {
            "dataframe": mapped_df,
            "mapping": valid_mapping,
            "confidence": valid_confidence,
            "unmapped_columns": unmapped_columns,
            "missing_columns": missing_columns
        }
