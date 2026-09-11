import pandas as pd

from preprocessing.schema_mapper import SchemaMapper


data = {
    "ticket_number": ["UC-1", "UC-2", "UC-3"],

    "severity_level": ["High", "Medium", "Low"],

    "workflow_state": ["Done", "In Progress", "Open"],

    "created_on": [
        "2026-09-01",
        "2026-09-02",
        "2026-09-03"
    ],

    "target_finish": [
        "2026-09-05",
        "2026-09-06",
        "2026-09-07"
    ],

    "completed_on": [
        "2026-09-04",
        None,
        None
    ],

    "responsible_person": [
        "user_1",
        "user_2",
        "user_1"
    ],

    "title": [
        "Login failure",
        "API integration",
        "Database update"
    ],

    "details": [
        "Users cannot log in",
        "Waiting for external API",
        "Database schema needs changes"
    ],

    "team_notes": [
        "Authentication team investigating",
        "Vendor response still pending",
        None
    ],

    "blocked_by_task": [
        None,
        "UC-1",
        "UC-2"
    ],

    "blocking_task": [
        "UC-2",
        None,
        None
    ],

    "business_area": [
        "Platform",
        "Integration",
        "Database"
    ]
}


df = pd.DataFrame(data)

mapper = SchemaMapper()
result = mapper.map_schema(df)


print("\n--- Mapping ---")
print(result["mapping"])

print("\n--- Confidence ---")
print(result["confidence"])

print("\n--- Missing Columns ---")
print(result["missing_columns"])

print("\n--- Unmapped Columns ---")
print(result["unmapped_columns"])

print("\n--- Final Columns ---")
print(result["dataframe"].columns.tolist())

print("\n--- Text ---")
print(result["dataframe"]["text"].tolist())

print("\n--- Dependency ---")
print(result["dataframe"]["dependency"].tolist())