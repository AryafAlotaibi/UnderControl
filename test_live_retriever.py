import pandas as pd

from rag.build_rag import build_live_rag
from rag.retriever import LiveRetriever


df = pd.DataFrame([
    {
        "issue_key": "UC-1",
        "type": "Task",
        "status": "Done",
        "priority": "High",
        "assignee_id": "user_1",
        "due_date": "2026-09-01",
        "story_point": 3,
        "dependency": None,
        "text": "Authentication API completed",
    },
    {
        "issue_key": "UC-2",
        "type": "Bug",
        "status": "Blocked",
        "priority": "High",
        "assignee_id": "user_2",
        "due_date": "2026-09-05",
        "story_point": 8,
        "dependency": "UC-1",
        "text": "Payment integration is blocked by authentication API dependency",
    },
    {
        "issue_key": "UC-3",
        "type": "Task",
        "status": "In Progress",
        "priority": "Medium",
        "assignee_id": "user_2",
        "due_date": "2026-09-10",
        "story_point": 5,
        "dependency": "UC-2",
        "text": "Checkout implementation depends on payment integration",
    },
])


collection = build_live_rag(df)

retriever = LiveRetriever(
    collection
)

results = retriever.search(
    "Which high priority task is blocked and what does it depend on?",
    n_results=3,
)

for result in results:
    print(result)
    print()