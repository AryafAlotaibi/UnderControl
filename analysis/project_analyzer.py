
import pandas as pd


class ProjectAnalyzer:

    NUMERIC_COLUMNS = [
        "story_point",
        "resolution_time_minutes",
        "in_progress_minutes",
    ]

    DATE_COLUMNS = [
        "creation_date",
        "due_date",
        "resolution_date",
    ]

    RESOLVED_STATUSES = {
        "done",
        "closed",
        "resolved",
        "completed",
        "complete",
    }

    HIGH_PRIORITIES = {
        "high",
        "highest",
        "critical",
        "blocker",
    }

    def prepare_project(self, df):
        """
        Prepare the standardized project DataFrame
        and calculate deterministic project metrics.

        Invalid date and numeric values are converted
        and reported through the warnings list.
        """

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame.")

        df = df.copy()
        warnings = []

        # Convert dates and detect invalid values
        for column in self.DATE_COLUMNS:
            if column in df.columns:
                original_values = df[column]

                converted_values = pd.to_datetime(
                    original_values,
                    errors="coerce",
                )

                invalid_mask = (
                    original_values.notna()
                    & converted_values.isna()
                )

                if invalid_mask.any():
                    invalid_count = int(invalid_mask.sum())

                    warnings.append(
                        f"Column '{column}' contains "
                        f"{invalid_count} invalid date value(s)."
                    )

                df[column] = converted_values

        # Convert numeric values and detect invalid values
        for column in self.NUMERIC_COLUMNS:
            if column in df.columns:
                original_values = df[column]

                converted_values = pd.to_numeric(
                    original_values,
                    errors="coerce",
                )

                invalid_mask = (
                    original_values.notna()
                    & converted_values.isna()
                )

                if invalid_mask.any():
                    invalid_count = int(invalid_mask.sum())

                    warnings.append(
                        f"Column '{column}' contains "
                        f"{invalid_count} invalid numeric value(s)."
                    )

                df[column] = converted_values

        metrics = self._calculate_metrics(df)

        return {
            "dataframe": df,
            "metrics": metrics,
            "warnings": warnings,
        }

    def _calculate_metrics(self, df):

        return {
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
                self._average(
                    df,
                    "resolution_time_minutes",
                ),

            "average_in_progress_time_minutes":
                self._average(
                    df,
                    "in_progress_minutes",
                ),

            "story_point_statistics":
                self._numeric_stats(
                    df,
                    "story_point",
                ),

            "tasks_per_assignee":
                self._value_counts(
                    df,
                    "assignee_id",
                ),

            "dependency_count":
                self._dependency_count(df),

            "schedule_signals": {
                "overdue_tasks":
                    self._overdue_count(df),

                "blocked_tasks":
                    self._blocked_count(df),

                "unfinished_high_priority_tasks":
                    self._unfinished_high_priority_count(df),
            },
        }

    def _value_counts(self, df, column):

        if column not in df.columns:
            return {}

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        values = values[values != ""]

        return values.value_counts().to_dict()

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
            "maximum": float(values.max()),
        }

    def _resolved_mask(self, df):

        mask = pd.Series(
            False,
            index=df.index,
            dtype=bool,
        )

        has_resolution_signal = False

        if "resolution_date" in df.columns:
            mask |= df["resolution_date"].notna()
            has_resolution_signal = True

        if "resolution" in df.columns:
            resolution = (
                df["resolution"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            valid_resolution = (
                (resolution != "")
                & (~resolution.isin({
                    "unresolved",
                    "none",
                    "null",
                    "nan",
                }))
            )

            mask |= valid_resolution
            has_resolution_signal = True

        if "status" in df.columns:
            status = (
                df["status"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            mask |= status.isin(
                self.RESOLVED_STATUSES
            )

            has_resolution_signal = True

        if not has_resolution_signal:
            return None

        return mask

    def _resolved_count(self, df):

        resolved_mask = self._resolved_mask(df)

        if resolved_mask is None:
            return None

        return int(resolved_mask.sum())

    def _unresolved_count(self, df):

        resolved_mask = self._resolved_mask(df)

        if resolved_mask is None:
            return None

        return int((~resolved_mask).sum())

    def _dependency_count(self, df):

        if "dependency" not in df.columns:
            return None

        values = (
            df["dependency"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        return int((values != "").sum())

    def _overdue_count(self, df):

        if "due_date" not in df.columns:
            return None

        resolved_mask = self._resolved_mask(df)

        if resolved_mask is None:
            return None

        now = pd.Timestamp.now()

        overdue_mask = (
            df["due_date"].notna()
            & (df["due_date"] < now)
            & (~resolved_mask)
        )

        return int(overdue_mask.sum())

    def _blocked_count(self, df):

        if "status" not in df.columns:
            return None

        status = (
            df["status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return int(
            (status == "blocked").sum()
        )

    def _unfinished_high_priority_count(self, df):

        if "priority" not in df.columns:
            return None

        resolved_mask = self._resolved_mask(df)

        if resolved_mask is None:
            return None

        priority = (
            df["priority"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        high_priority_mask = priority.isin(
            self.HIGH_PRIORITIES
        )

        unfinished_mask = (
            high_priority_mask
            & (~resolved_mask)
        )

        return int(unfinished_mask.sum())