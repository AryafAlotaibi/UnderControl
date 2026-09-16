# import uuid

# import chromadb
# import pandas as pd
# from sentence_transformers import SentenceTransformer


# EMBED_MODEL = "all-MiniLM-L6-v2"

# _embedder = None


# CORE_COLUMNS = {
#     "issue_id",
#     "issue_key",
#     "project_key",
#     "project_name",
#     "type",
#     "priority",
#     "status",
#     "resolution",
#     "creation_date",
#     "due_date",
#     "resolution_date",
#     "story_point",
#     "resolution_time_minutes",
#     "in_progress_minutes",
#     "assignee_id",
#     "text",
#     "description",
#     "comments",
#     "dependency",
#     "blocks",
# }


# def get_embedder():
#     """
#     Load the embedding model once and reuse it
#     across Live RAG builds and queries.
#     """
#     global _embedder

#     if _embedder is None:
#         _embedder = SentenceTransformer(EMBED_MODEL)

#     return _embedder


# def clean_value(value):
#     """
#     Convert missing values to empty strings and
#     return safe string values for Chroma.
#     """
#     if value is None:
#         return ""

#     try:
#         if pd.isna(value):
#             return ""
#     except (TypeError, ValueError):
#         pass

#     return str(value).strip()


# def row_to_text(row):
#     """
#     Convert one standardized project issue into
#     readable text for semantic retrieval.
#     """
#     lines = []

#     issue_key = (
#         clean_value(row.get("issue_key"))
#         or clean_value(row.get("issue_id"))
#         or "Unknown"
#     )

#     lines.append(f"Issue: {issue_key}")

#     structured_fields = [
#         ("Project", row.get("project_name")),
#         ("Project Key", row.get("project_key")),
#         ("Type", row.get("type")),
#         ("Status", row.get("status")),
#         ("Priority", row.get("priority")),
#         ("Resolution", row.get("resolution")),
#         ("Assignee", row.get("assignee_id")),
#         ("Created", row.get("creation_date")),
#         ("Due Date", row.get("due_date")),
#         ("Resolved", row.get("resolution_date")),
#         ("Story Points", row.get("story_point")),
#         (
#             "Resolution Time Minutes",
#             row.get("resolution_time_minutes"),
#         ),
#         (
#             "In Progress Minutes",
#             row.get("in_progress_minutes"),
#         ),
#     ]

#     for label, value in structured_fields:
#         value = clean_value(value)

#         if value:
#             lines.append(f"{label}: {value}")

#     content_parts = []

#     for column in (
#         "text",
#         "description",
#         "comments",
#     ):
#         value = clean_value(row.get(column))

#         if value:
#             content_parts.append(value)

#     if content_parts:
#         lines.append(
#             "Content: " + " | ".join(content_parts)
#         )

#     dependency = clean_value(
#         row.get("dependency")
#     )

#     blocks = clean_value(
#         row.get("blocks")
#     )

#     if dependency:
#         lines.append(
#             f"Blocked by: {dependency}"
#         )

#     if blocks:
#         lines.append(
#             f"Blocks: {blocks}"
#         )

#     additional_fields = []

#     for column, value in row.items():
#         if column in CORE_COLUMNS:
#             continue

#         value = clean_value(value)

#         if value:
#             additional_fields.append(
#                 f"{column}: {value}"
#             )

#     if additional_fields:
#         lines.append(
#             "Additional fields: "
#             + " | ".join(additional_fields)
#         )

#     return "\n".join(lines)


# def build_live_rag(standardized_df):
#     """
#     Build a temporary in-memory Chroma collection
#     from the standardized project DataFrame.

#     A new collection is created for every analysis run.
#     Nothing is persisted to disk.
#     """
#     if not isinstance(
#         standardized_df,
#         pd.DataFrame,
#     ):
#         raise TypeError(
#             "standardized_df must be a pandas DataFrame."
#         )

#     if standardized_df.empty:
#         raise ValueError(
#             "Cannot build Live RAG from an empty DataFrame."
#         )

#     client = chromadb.Client()

#     collection = client.create_collection(
#         name=f"live_project_{uuid.uuid4().hex}",
#         metadata={
#             "hnsw:space": "cosine"
#         },
#     )

#     ids = []
#     documents = []
#     metadatas = []

#     for index, (_, row) in enumerate(
#         standardized_df.iterrows()
#     ):
#         row_dict = row.to_dict()

#         document = row_to_text(
#             row_dict
#         )

#         issue_key = (
#             clean_value(
#                 row_dict.get("issue_key")
#             )
#             or clean_value(
#                 row_dict.get("issue_id")
#             )
#             or f"row_{index}"
#         )

#         ids.append(
#             f"live_{index}"
#         )

#         documents.append(
#             document
#         )

#         metadatas.append({
#             "issue_key": issue_key,
#             "status": (
#                 clean_value(
#                     row_dict.get("status")
#                 )
#                 or "Unknown"
#             ),
#             "priority": (
#                 clean_value(
#                     row_dict.get("priority")
#                 )
#                 or "Unknown"
#             ),
#             "assignee_id": (
#                 clean_value(
#                     row_dict.get("assignee_id")
#                 )
#                 or "Unknown"
#             ),
#         })

#     embedder = get_embedder()

#     embeddings = embedder.encode(
#         documents,
#         normalize_embeddings=True,
#     ).tolist()

#     collection.add(
#         ids=ids,
#         embeddings=embeddings,
#         documents=documents,
#         metadatas=metadatas,
#     )

#     return collection



import uuid

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer


EMBED_MODEL = "all-MiniLM-L6-v2"

# Process embeddings in batches to improve performance
EMBED_BATCH_SIZE = 64

_embedder = None


CORE_COLUMNS = {
    "issue_id",
    "issue_key",
    "project_key",
    "project_name",
    "type",
    "priority",
    "status",
    "resolution",
    "creation_date",
    "due_date",
    "resolution_date",
    "story_point",
    "resolution_time_minutes",
    "in_progress_minutes",
    "assignee_id",
    "text",
    "description",
    "comments",
    "dependency",
    "blocks",
}


def get_embedder():
    """
    Load the embedding model once and reuse it
    across Live RAG builds and queries.
    """
    global _embedder

    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)

    return _embedder


def clean_value(value):
    """
    Convert missing values to empty strings and
    return safe string values for Chroma.
    """
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def row_to_text(row):
    """
    Convert one standardized project issue into
    readable text for semantic retrieval.
    """
    lines = []

    issue_key = (
        clean_value(row.get("issue_key"))
        or clean_value(row.get("issue_id"))
        or "Unknown"
    )

    lines.append(f"Issue: {issue_key}")

    structured_fields = [
        ("Project", row.get("project_name")),
        ("Project Key", row.get("project_key")),
        ("Type", row.get("type")),
        ("Status", row.get("status")),
        ("Priority", row.get("priority")),
        ("Resolution", row.get("resolution")),
        ("Assignee", row.get("assignee_id")),
        ("Created", row.get("creation_date")),
        ("Due Date", row.get("due_date")),
        ("Resolved", row.get("resolution_date")),
        ("Story Points", row.get("story_point")),
        (
            "Resolution Time Minutes",
            row.get("resolution_time_minutes"),
        ),
        (
            "In Progress Minutes",
            row.get("in_progress_minutes"),
        ),
    ]

    for label, value in structured_fields:
        value = clean_value(value)

        if value:
            lines.append(f"{label}: {value}")

    content_parts = []

    for column in (
        "text",
        "description",
        "comments",
    ):
        value = clean_value(row.get(column))

        if value:
            content_parts.append(value)

    if content_parts:
        lines.append(
            "Content: " + " | ".join(content_parts)
        )

    dependency = clean_value(
        row.get("dependency")
    )

    blocks = clean_value(
        row.get("blocks")
    )

    if dependency:
        lines.append(
            f"Blocked by: {dependency}"
        )

    if blocks:
        lines.append(
            f"Blocks: {blocks}"
        )

    additional_fields = []

    for column, value in row.items():
        if column in CORE_COLUMNS:
            continue

        value = clean_value(value)

        if value:
            additional_fields.append(
                f"{column}: {value}"
            )

    if additional_fields:
        lines.append(
            "Additional fields: "
            + " | ".join(additional_fields)
        )

    return "\n".join(lines)


def build_live_rag(standardized_df):
    """
    Build a temporary in-memory Chroma collection
    from the standardized project DataFrame.

    A new collection is created for every analysis run.
    Nothing is persisted to disk.

    Embeddings and Chroma inserts are processed
    in batches to improve performance.
    """
    if not isinstance(
        standardized_df,
        pd.DataFrame,
    ):
        raise TypeError(
            "standardized_df must be a pandas DataFrame."
        )

    if standardized_df.empty:
        raise ValueError(
            "Cannot build Live RAG from an empty DataFrame."
        )

    client = chromadb.Client()

    collection = client.create_collection(
        name=f"live_project_{uuid.uuid4().hex}",
        metadata={
            "hnsw:space": "cosine"
        },
    )

    ids = []
    documents = []
    metadatas = []

    for index, (_, row) in enumerate(
        standardized_df.iterrows()
    ):
        row_dict = row.to_dict()

        document = row_to_text(
            row_dict
        )

        issue_key = (
            clean_value(
                row_dict.get("issue_key")
            )
            or clean_value(
                row_dict.get("issue_id")
            )
            or f"row_{index}"
        )

        ids.append(
            f"live_{index}"
        )

        documents.append(
            document
        )

        metadatas.append({
            "issue_key": issue_key,
            "status": (
                clean_value(
                    row_dict.get("status")
                )
                or "Unknown"
            ),
            "priority": (
                clean_value(
                    row_dict.get("priority")
                )
                or "Unknown"
            ),
            "assignee_id": (
                clean_value(
                    row_dict.get("assignee_id")
                )
                or "Unknown"
            ),
        })

    # Load the embedding model once and reuse it.
    embedder = get_embedder()

    total_documents = len(documents)

    # Process documents in batches instead of
    # embedding the entire project at once.
    for start in range(
        0,
        total_documents,
        EMBED_BATCH_SIZE,
    ):
        end = min(
            start + EMBED_BATCH_SIZE,
            total_documents,
        )

        batch_documents = documents[start:end]
        batch_ids = ids[start:end]
        batch_metadatas = metadatas[start:end]

        batch_embeddings = embedder.encode(
            batch_documents,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )

    return collection