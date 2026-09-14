from rag.retriever import GroundTruthRetriever


retriever = GroundTruthRetriever()

results = retriever.search(
    "blocked high priority tasks causing project delays",
    n_results=3,
)

for result in results:
    print(result)
    print()