import pandas as pd
from preprocessing.schema_mapper import SchemaMapper


# بيانات تجريبية بأسماء أعمدة مختلفة عن الـschema حقنا
data = {
    "ticket_number": ["T-1", "T-2", "T-3"],
    "project": ["UnderControl", "UnderControl", "UnderControl"],
    "severity": ["High", "Medium", "Low"],
    "current_state": ["Done", "In Progress", "Open"],
    "opened_at": ["2026-01-01", "2026-01-02", "2026-01-03"],
    "closed_at": ["2026-01-05", None, None],
    "points": [5, 8, 3],
    "owner": ["user_1", "user_2", "user_1"],
    "description": [
        "Login issue",
        "API integration task",
        "Database bug"
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