def build_sql_prompt(question: str, schema: str) -> str:
    return f"""### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- Use only the tables and columns provided in the database schema below.
- If the question cannot be answered using only this schema, return 'I do not know'.
- Do not assume extra tables or columns.
- Return only the SQL query inside [SQL]...[/SQL] tags.

### Database Schema
{schema}

### Answer
[SQL]
"""

def build_sql_correction_prompt(question: str, sql_code: str, schema: str) -> str:
    return f"""
You are a SQL expert.
Your task is to CORRECT the following SQL query so that it perfectly answers the question using STRICTLY and ONLY the provided database schema.

RULES:
- Use ONLY tables and columns that exist in the schema.
- Use common SQL aggregate functions like MAX(), MIN(), COUNT(), SUM() when relevant.
- DO NOT invent or assume any tables, columns, relationships, or JOINs that do not exist.
- If the question CANNOT be answered using ONLY the schema, return exactly: SELECT 'Not possible';
- Return ONLY the corrected SQL query (NO explanation, NO code block, NO comments, NO extra text).

Question:
{question}

SQL query to correct:
{sql_code}

Database schema:
{schema}
"""


def build_sql_validator_prompt(question: str, sql_code: str, schema: str) -> str:
    return f"""Schema:
{schema}

Question:
{question}

SQL Candidate:
{sql_code}

-- Correct SQL:
"""
