def build_schema_mapping_prompt(standard_schema, user_columns, column_samples):

    return f"""
You are a schema mapping assistant.

Your task is to map the user's CSV columns to the standard schema.

STANDARD SCHEMA:
{standard_schema}

USER COLUMNS:
{user_columns}

SAMPLE VALUES:
{column_samples}

Rules:
- Understand columns based on both their names and sample values.
- Map only when the meaning is reasonably clear.
- Do not invent mappings.
- Each user column can map to only one standard column.
- If a column does not match, mark it as unmapped.
- If a standard column is not available, mark it as missing.
- Return JSON only.

Return exactly this structure:

{{
    "mapping": {{
        "user_column": "standard_column"
    }},
    "confidence": {{
        "user_column": 0.0
    }},
    "unmapped_columns": [],
    "missing_columns": []
}}
"""
