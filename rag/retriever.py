# import json
# import os
# from pathlib import Path

# import chromadb
# from langchain_classic.tools import tool

# from rag.build_rag import get_embedder


# GROUND_TRUTH_COLLECTION = "ground_truth_tawos"

# PROJECT_ROOT = Path(__file__).resolve().parent.parent
# DEFAULT_GROUND_TRUTH_PATH = (
#     PROJECT_ROOT
#     / "data"
#     / "ground_truth_rag_db"
# )


# def search_collection(
#     collection,
#     query,
#     n_results=5,
# ):
#     """
#     Search a Chroma collection using the same embedding
#     model used to build the RAG indexes.
#     """
#     if not query or not query.strip():
#         raise ValueError(
#             "Search query cannot be empty."
#         )

#     collection_size = collection.count()

#     if collection_size == 0:
#         return []

#     n_results = min(
#         n_results,
#         collection_size,
#     )

#     embedder = get_embedder()

#     query_embedding = embedder.encode(
#         [query],
#         normalize_embeddings=True,
#     ).tolist()

#     results = collection.query(
#         query_embeddings=query_embedding,
#         n_results=n_results,
#         include=[
#             "documents",
#             "metadatas",
#             "distances",
#         ],
#     )

#     matches = []

#     for document, metadata, distance in zip(
#         results["documents"][0],
#         results["metadatas"][0],
#         results["distances"][0],
#     ):
#         matches.append({
#             "document": document,
#             "metadata": metadata,
#             "distance": float(distance),
#         })

#     return matches


# class LiveRetriever:
#     """
#     Retrieve relevant issues from the current project's
#     temporary Live RAG collection.
#     """

#     def __init__(self, collection):
#         self.collection = collection

#     def search(
#         self,
#         query,
#         n_results=5,
#     ):
#         return search_collection(
#             collection=self.collection,
#             query=query,
#             n_results=n_results,
#         )


# class GroundTruthRetriever:
#     """
#     Retrieve historical project evidence from the
#     persistent Ground Truth RAG.
#     """

#     def __init__(
#         self,
#         rag_path=None,
#         collection_name=GROUND_TRUTH_COLLECTION,
#     ):
#         path = (
#             rag_path
#             or os.getenv(
#                 "GROUND_TRUTH_RAG_PATH"
#             )
#             or DEFAULT_GROUND_TRUTH_PATH
#         )

#         self.client = chromadb.PersistentClient(
#             path=str(path)
#         )

#         self.collection = (
#             self.client.get_collection(
#                 collection_name
#             )
#         )

#     def search(
#         self,
#         query,
#         n_results=5,
#     ):
#         return search_collection(
#             collection=self.collection,
#             query=query,
#             n_results=n_results,
#         )


# def build_live_rag_tool(
#     live_collection,
# ):
#     """
#     Build a LangChain tool for searching the current project.
#     """
#     retriever = LiveRetriever(
#         live_collection
#     )

#     @tool
#     def search_live_project(
#         query: str,
#     ) -> str:
#         """
#         Search detailed evidence from the current project,
#         including tasks, statuses, priorities, dependencies,
#         assignees, dates, and issue text.
#         """
#         results = retriever.search(
#             query=query,
#             n_results=5,
#         )

#         return json.dumps(
#             results,
#             ensure_ascii=False,
#             indent=2,
#             default=str,
#         )

#     return search_live_project


# def build_ground_truth_rag_tool(
#     ground_truth_retriever,
# ):
#     """
#     Build a LangChain tool for searching historical evidence.
#     """

#     @tool
#     def search_ground_truth(
#         query: str,
#     ) -> str:
#         """
#         Search historical project cases from the Ground Truth RAG.
#         Historical results are supporting context only and must
#         not be treated as facts about the current project.
#         """
#         results = ground_truth_retriever.search(
#             query=query,
#             n_results=5,
#         )

#         return json.dumps(
#             results,
#             ensure_ascii=False,
#             indent=2,
#             default=str,
#         )

#     return search_ground_truth
import json
import os
from pathlib import Path

import chromadb
from langchain_classic.tools import tool

from rag.build_rag import get_embedder


GROUND_TRUTH_COLLECTION = "ground_truth_tawos"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "ground_truth_rag_db"
)


LIVE_FILTER_FIELDS = {
    "issue_key",
    "status",
    "priority",
    "assignee_id",
}


# =========================================================
# Semantic Search
# =========================================================

def search_collection(
    collection,
    query,
    n_results=5,
):
    """
    Perform semantic search over a Chroma collection.
    """

    if not query or not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    collection_size = collection.count()

    if collection_size == 0:
        return []

    n_results = min(
        n_results,
        collection_size,
    )

    embedder = get_embedder()

    query_embedding = embedder.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    matches = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        matches.append({
            "document": document,
            "metadata": metadata,
            "distance": float(distance),
        })

    return matches


# =========================================================
# Metadata Filtering
# =========================================================

def _normalize_filter_values(value):
    """
    Normalize one metadata filter value into a list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    value = str(value).strip()

    if not value:
        return []

    return [value]


def _build_where_filter(filters):
    """
    Build a Chroma metadata where-filter.
    """

    conditions = []

    for field in LIVE_FILTER_FIELDS:

        values = _normalize_filter_values(
            filters.get(field)
        )

        if not values:
            continue

        if len(values) == 1:
            conditions.append({
                field: {
                    "$eq": values[0]
                }
            })

        else:
            conditions.append({
                field: {
                    "$in": values
                }
            })

    if not conditions:
        raise ValueError(
            "At least one valid metadata filter is required."
        )

    if len(conditions) == 1:
        return conditions[0]

    return {
        "$and": conditions
    }


def filter_collection(
    collection,
    filters,
    limit=50,
):
    """
    Retrieve project issues using exact metadata filters.
    """

    where_filter = _build_where_filter(
        filters
    )

    results = collection.get(
        where=where_filter,
        limit=limit,
        include=[
            "documents",
            "metadatas",
        ],
    )

    matches = []

    documents = results.get(
        "documents",
        [],
    )

    metadatas = results.get(
        "metadatas",
        [],
    )

    for document, metadata in zip(
        documents,
        metadatas,
    ):
        matches.append({
            "document": document,
            "metadata": metadata,
        })

    return matches


# =========================================================
# Live Retriever
# =========================================================

class LiveRetriever:
    """
    Retrieve evidence from the current project's
    temporary Live RAG collection.
    """

    def __init__(self, collection):
        self.collection = collection

    def search(
        self,
        query,
        n_results=5,
    ):
        return search_collection(
            collection=self.collection,
            query=query,
            n_results=n_results,
        )

    def filter(
        self,
        filters,
        limit=50,
    ):
        return filter_collection(
            collection=self.collection,
            filters=filters,
            limit=limit,
        )


# =========================================================
# Ground Truth Retriever
# =========================================================

class GroundTruthRetriever:
    """
    Retrieve historical project evidence from the
    persistent Ground Truth RAG.
    """

    def __init__(
        self,
        rag_path=None,
        collection_name=GROUND_TRUTH_COLLECTION,
    ):
        path = (
            rag_path
            or os.getenv(
                "GROUND_TRUTH_RAG_PATH"
            )
            or DEFAULT_GROUND_TRUTH_PATH
        )

        self.client = chromadb.PersistentClient(
            path=str(path)
        )

        self.collection = (
            self.client.get_collection(
                collection_name
            )
        )

    def search(
        self,
        query,
        n_results=5,
    ):
        return search_collection(
            collection=self.collection,
            query=query,
            n_results=n_results,
        )


# =========================================================
# Live RAG Tool
# =========================================================

def build_live_rag_tool(
    live_collection,
):
    """
    Build the Live RAG tool used by the Analysis Agent.
    """

    retriever = LiveRetriever(
        live_collection
    )

    @tool
    def search_live_project(
        request: str,
    ) -> str:
        """
        Search the current project.

        Use semantic mode for open-ended evidence:

        {"mode": "semantic",
         "query": "tasks causing database delays"}

        Use filter mode when exact project records are needed:

        {"mode": "filter",
         "status": ["Blocked"]}

        Multiple filters can be combined:

        {"mode": "filter",
         "status": ["Blocked"],
         "priority": ["High", "Highest"]}

        Supported exact filters:
        issue_key, status, priority, assignee_id.
        """

        try:
            payload = json.loads(
                request
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            payload = {
                "mode": "semantic",
                "query": request,
            }

        mode = str(
            payload.get(
                "mode",
                "semantic",
            )
        ).strip().lower()

        if mode == "filter":

            filters = {
                field: payload.get(field)
                for field in LIVE_FILTER_FIELDS
                if payload.get(field) is not None
            }

            results = retriever.filter(
                filters=filters,
            )

            response = {
                "mode": "filter",
                "filters": filters,
                "returned_count": len(results),
                "results": results,
            }

        else:

            query = str(
                payload.get(
                    "query",
                    "",
                )
            ).strip()

            results = retriever.search(
                query=query,
                n_results=5,
            )

            response = {
                "mode": "semantic",
                "query": query,
                "returned_count": len(results),
                "results": results,
            }

        return json.dumps(
            response,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    return search_live_project


# =========================================================
# Ground Truth RAG Tool
# =========================================================

def build_ground_truth_rag_tool(
    ground_truth_retriever,
):
    """
    Build a LangChain tool for searching historical evidence.
    """

    @tool
    def search_ground_truth(
        query: str,
    ) -> str:
        """
        Search historical project cases from the Ground Truth RAG.

        Historical results are supporting context only
        and must not be treated as facts about the
        current project.
        """

        results = ground_truth_retriever.search(
            query=query,
            n_results=5,
        )

        return json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    return search_ground_truth