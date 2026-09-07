class SchemaMapper:

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
        "resolution_date": "Date and time when the issue was resolved or completed",
        "story_point": "Estimated effort expressed in story points",
        "resolution_time_minutes": "Total time required to resolve the issue in minutes",
        "in_progress_minutes": "Time the issue spent in progress in minutes",
        "assignee_id": "Identifier of the person responsible for the issue",
        "text": "Issue title, description, summary, or textual content",
        "dependency": "Dependency, blocking, or linked-issue relationship"
    }

    def __init__(self, llm=None):
        self.llm = llm

    def get_column_samples(self, df, sample_size=3):
        """
        Get sample values from each user column
        to help the LLM understand its meaning.
        """

        samples = {}

        for column in df.columns:
            samples[column] = (
                df[column]
                .dropna()
                .astype(str)
                .head(sample_size)
                .tolist()
            )

        return samples

    def get_schema_info(self, df):
        """
        Prepare user columns and sample values
        before sending them to the LLM.
        """

        return {
            "user_columns": list(df.columns),
            "column_samples": self.get_column_samples(df),
            "standard_schema": self.STANDARD_SCHEMA
        }

    def apply_mapping(self, df, mapping):
        """
        Rename user columns using the mapping
        returned by the LLM.
        """

        valid_mapping = {}

        for user_column, standard_column in mapping.items():

            if (
                user_column in df.columns
                and standard_column in self.STANDARD_SCHEMA
            ):
                valid_mapping[user_column] = standard_column

        mapped_df = df.rename(columns=valid_mapping)

        return mapped_df

    def get_missing_columns(self, df):
        """
        Find standard columns that were not found
        after schema mapping.
        """

        return [
            column
            for column in self.STANDARD_SCHEMA
            if column not in df.columns
        ]

    def get_unmapped_columns(self, original_df, mapping):
        """
        Find user columns that the LLM
        could not map to our standard schema.
        """

        return [
            column
            for column in original_df.columns
            if column not in mapping
        ]

    def map_schema(self, df):
        """
        Main schema mapping step.

        Later, this method will send the schema information
        to the LLM and receive the column mapping.
        """

        schema_info = self.get_schema_info(df)

        # Next step:
        # Send schema_info to the LLM
        # and receive something like:
        #
        # {
        #     "ticket_id": "issue_id",
        #     "severity": "priority",
        #     "assigned_user": "assignee_id",
        #     "created_at": "creation_date",
        #     "description": "text"
        # }

        return schema_info
