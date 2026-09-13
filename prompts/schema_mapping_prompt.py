def build_schema_mapping_prompt(
    standard_schema,
    user_columns,
    column_samples
):
    return f"""
You are the schema-mapping component of UnderControl.

Your task is to map columns from an arbitrary project CSV to the
UnderControl standard schema based on semantic meaning.

STANDARD SCHEMA:
{standard_schema}

USER COLUMNS:
{user_columns}

COLUMN SAMPLES:
{column_samples}

Instructions:
- Infer each column's meaning using its name and sample values.
- Map it to a standard field only when the semantic match is clear.
- Do not infer or fabricate information that is not present in the data.
- Each source column may map to at most one standard field.
- Standard fields are normally one-to-one.
- "text" and "dependency" may receive multiple source columns when
  several columns contain relevant information for those fields.
- Distinguish planned deadlines ("due_date") from actual completion
  dates ("resolution_date").
- Distinguish internal identifiers ("issue_id") from readable task or
  ticket keys ("issue_key") when the evidence allows.
- Columns that do not map confidently to the standard schema should
  remain unmapped; they will still be preserved downstream.
- Assign a confidence score from 0.0 to 1.0 to each proposed mapping.
- Return valid JSON only.

Output format:

{{
    "mapping": {{
        "source_column": "standard_field"
    }},
    "confidence": {{
        "source_column": 0.0
    }}
}}
"""