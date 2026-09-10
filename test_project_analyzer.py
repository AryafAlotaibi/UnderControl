import pandas as pd

from preprocessing.schema_mapper import SchemaMapper
from analysis.project_analyzer import ProjectAnalyzer


data = {
    "ticket_number": ["T-1", "T-2", "T-3"],
    "project_code": ["UC", "UC", "UC"],
    "project": ["UnderControl", "UnderControl", "UnderControl"],

    "work_item_type": ["Bug", "Task", "Bug"],

    "severity": ["High", "Medium", "High"],
    "current_state": ["Done", "In Progress", "Open"],

    "resolution_status": ["Fixed", None, None],

    "opened_at": [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03"
    ],

    "closed_at": [
        "2026-01-05",
        None,
        None
    ],

    "points": [5, 8, 3],

    "time_to_resolve": [5760, None, None],
    "active_work_minutes": [2100, 3200, 1500],

    "owner": ["user_1", "user_2", "user_1"],

    "description": [
        "Login issue",
        "API integration task",
        "Database bug"
    ],

    "blocked_by": [
        None,
        "T-1",
        "T-2"
    ]
}


df = pd.DataFrame(data)


# Step 1: Standardize user columns
mapper = SchemaMapper()
mapping_result = mapper.map_schema(df)

standardized_df = mapping_result["dataframe"]


print("\n--- Standardized Columns ---")
print(standardized_df.columns.tolist())


# Step 2: Calculate project facts
analyzer = ProjectAnalyzer()
analysis_result = analyzer.prepare_project(standardized_df)


print("\n--- Project Metrics ---")
print(analysis_result["metrics"])