import pandas as pd


class ProjectAnalyzer:

    NUMERIC_COLUMNS = [
        "story_point",
        "resolution_time_minutes",
        "in_progress_minutes"
    ]

    DATE_COLUMNS = [
        "creation_date",
        "resolution_date"
    ]

    def prepare_project(self, df):
        """
        Prepare the standardized DataFrame for analysis.

        This step only:
        - Converts dates
        - Converts numeric columns
        - Calculates factual project metrics

        It does NOT detect root causes or bottlenecks.
        """

        df = df.copy()

        # Convert date columns
        for column in self.DATE_COLUMNS:
            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

        # Convert numeric columns
        for column in self.NUMERIC_COLUMNS:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        metrics = self._calculate_metrics(df)

        return {
            "dataframe": df,
            "metrics": metrics
        }


    def _calculate_metrics(self, df):

        metrics = {
            "total_issues": int(len(df)),

            "status_distribution":
                self._value_counts(df, "status"),

            "priority_distribution":
                self._value_counts(df, "priority"),

            "type_distribution":
                self._value_counts(df, "type"),

            "resolved_issues":
                self._resolved_count(df),

            "unresolved_issues":
                self._unresolved_count(df),

            "average_resolution_time_minutes":
                self._average(df, "resolution_time_minutes"),

            "average_in_progress_time_minutes":
                self._average(df, "in_progress_minutes"),

            "story_point_statistics":
                self._numeric_stats(df, "story_point"),

            "tasks_per_assignee":
                self._value_counts(df, "assignee_id"),

            "dependency_count":
                self._dependency_count(df)
        }

        return metrics


    def _value_counts(self, df, column):

        if column not in df.columns:
            return {}

        return (
            df[column]
            .dropna()
            .astype(str)
            .value_counts()
            .to_dict()
        )


    def _average(self, df, column):

        if column not in df.columns:
            return None

        values = df[column].dropna()

        if values.empty:
            return None

        return float(values.mean())


    def _numeric_stats(self, df, column):

        if column not in df.columns:
            return {}

        values = df[column].dropna()

        if values.empty:
            return {}

        return {
            "average": float(values.mean()),
            "minimum": float(values.min()),
            "maximum": float(values.max())
        }


    def _resolved_count(self, df):

        if "resolution_date" in df.columns:
            return int(df["resolution_date"].notna().sum())

        if "resolution" in df.columns:
            return int(df["resolution"].notna().sum())

        return None


    def _unresolved_count(self, df):

        resolved = self._resolved_count(df)

        if resolved is None:
            return None

        return int(len(df) - resolved)


    def _dependency_count(self, df):

        if "dependency" not in df.columns:
            return None

        values = df["dependency"].dropna().astype(str)

        values = values[
            values.str.strip() != ""
        ]

        return int(len(values))