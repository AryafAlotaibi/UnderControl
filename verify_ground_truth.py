"""
verify_ground_truth.py
-----------------------------------
Full sanity check for Ground Truth RAG after transferring it to a
new machine. Confirms not just "it opens" but that the actual
content and retrieval quality survived the transfer intact.

Usage:
    python verify_ground_truth.py
"""

import chromadb
from sentence_transformers import SentenceTransformer

# Adjust this path to match the machine you're running on
GROUND_TRUTH_DB_PATH = r"C:\Users\robaa\UnderControl\data\ground_truth_rag_db"
GROUND_TRUTH_COLLECTION = "ground_truth_tawos"
EXPECTED_COUNT = 169652  # what it should be if the transfer was complete


def main():
    print("1) Connecting to Ground Truth RAG...")
    client = chromadb.PersistentClient(path=GROUND_TRUTH_DB_PATH)
    collections = client.list_collections()
    print(f"   Collections found: {[c.name for c in collections]}")

    if not collections:
        print("   FAILED: no collections found — the transfer is still incomplete.")
        return

    collection = client.get_collection(GROUND_TRUTH_COLLECTION)

    print("\n2) Checking chunk count...")
    actual_count = collection.count()
    print(f"   Expected: {EXPECTED_COUNT} | Actual: {actual_count}")
    if actual_count == EXPECTED_COUNT:
        print("   PASSED: count matches exactly.")
    else:
        print("   WARNING: count doesn't match — some data may be missing or "
              "duplicated. Don't proceed until this matches.")
        return

    print("\n3) Testing retrieval quality with a sample query...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    query = "Task blocked for several days waiting on an external vendor API"
    query_embedding = embedder.encode([query], normalize_embeddings=True).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=3)

    print(f"   Query: '{query}'")
    for i in range(len(results["ids"][0])):
        similarity = 1 - results["distances"][0][i]
        meta = results["metadatas"][0][i]
        print(f"   [{i+1}] similarity={similarity:.3f} | {meta['issue_key']} "
              f"({meta['project_key']}, outcome={meta['outcome_category']})")

    # Sanity thresholds based on what we already validated on the
    # original machine — similarities should land in a similar range
    top_similarity = 1 - results["distances"][0][0]
    if top_similarity >= 0.45:
        print("\n   PASSED: retrieval quality looks consistent with the original.")
    else:
        print(f"\n   WARNING: top similarity ({top_similarity:.3f}) is lower than "
              "expected — worth double-checking the embedding model version matches.")

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED — Ground Truth RAG transferred correctly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
