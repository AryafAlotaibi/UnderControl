import json

import pandas as pd

from pipeline.pipeline import run_analysis


df = pd.DataFrame([
    {
        "issue_key": "UC-1",
        "project_key": "UC",
        "project_name": "UnderControl Test",
        "type": "Bug",
        "priority": "High",
        "status": "Blocked",
        "resolution": None,
        "creation_date": "2026-08-01",
        "resolution_date": None,
        "story_point": 8,
        "resolution_time_minutes": None,
        "in_progress_minutes": 5000,
        "assignee_id": "user_1",
        "text": "Backend API is blocked by unfinished database changes.",
        "dependency": "UC-2",
    },
    {
        "issue_key": "UC-2",
        "project_key": "UC",
        "project_name": "UnderControl Test",
        "type": "Task",
        "priority": "High",
        "status": "In Progress",
        "resolution": None,
        "creation_date": "2026-07-25",
        "resolution_date": None,
        "story_point": 5,
        "resolution_time_minutes": None,
        "in_progress_minutes": 7000,
        "assignee_id": "user_2",
        "text": "Database migration is still incomplete.",
        "dependency": None,
    },
])


result = run_analysis(df)

print("\n--- Analysis Result ---")
print(json.dumps(result["analysis"], indent=2, ensure_ascii=False))

print("\n--- Simulation Result ---")
print(json.dumps(result["simulation"], indent=2, ensure_ascii=False))