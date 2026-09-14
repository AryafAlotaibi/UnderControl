"""
UnderControl Analysis Pipeline

Flow:
    User CSV
        -> SchemaMapper
        -> Standardized DataFrame

    Standardized DataFrame
        -> ProjectAnalyzer
        -> Project Metrics

    Standardized DataFrame
        -> Live RAG
        -> Live RAG Retriever

    Ground Truth RAG
        -> Ground Truth Retriever

    Project Metrics
    + Live RAG Retriever
    + Ground Truth Retriever
        -> Analysis Agent
        -> AnalysisOutput
"""