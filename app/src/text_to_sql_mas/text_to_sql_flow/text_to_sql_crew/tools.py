import os
from typing import Type, Dict, List

import psycopg2
import requests
from crewai_tools.tools.mdx_seach_tool.mdx_search_tool import MDXSearchTool
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from config.config import OMOP_SYNTHETIC_DB_PARAMS



class SchemaLinkingToolInput(BaseModel):
    tables_columns: Dict[str, list[str]] = Field(..., description="Dictionary that maps table names to column names")

class SchemaLinkingTool(BaseTool):
    name: str = "Schema Linking Tool"
    description: str = "Generates a concise schema description with example values and relationships found from a PostgreSQL database given the subset of tables and columns given."
    args_schema: Type[BaseModel] = SchemaLinkingToolInput

    def _run(self, tables: list[str], columns: list[str], query: str) -> str:
        # Connect to the PostgreSQL database

        conn = psycopg2.connect(**OMOP_SYNTHETIC_DB_PARAMS)

        cur = conn.cursor()

        def get_table_info(table_name):
            cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
            """, (table_name,))

            columns = cur.fetchall()

            cur.execute("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """, (table_name,))
            pk_columns = {row[0] for row in cur.fetchall()}

            cur.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            examples = cur.fetchall()

            schema_lines = []
            for i, (col_name, data_type) in enumerate(columns):
                example_vals = [str(row[i]) for row in examples]
                pk_str = ", Primary Key" if col_name in pk_columns else ""
                schema_lines.append(f"({col_name}:{data_type.upper()}{pk_str}, Examples: [{', '.join(example_vals)}])")
           
            return f"# table: {table_name}\n[\n" + ",\n".join(schema_lines) + "\n]"

        cur.execute("""
            SELECT
                tc.table_name AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name AS target_table,
                ccu.column_name AS target_column
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY';
        """)
        foreign_keys = cur.fetchall()

        tables = ['supplier', 'nation']
        schema_repr = "\n".join(get_table_info(table) for table in tables)

        fk_lines = [f"{src}.{src_col}→{tgt}.{tgt_col}" for src, src_col, tgt, tgt_col in foreign_keys]
        fk_repr = "\n[Foreign keys]\n" + "\n".join(fk_lines)

        print(schema_repr + fk_repr)

        cur.close()
        return schema_repr + fk_repr

# Initialize the tool with a specific MDX file path for an exclusive search within that document


class OMOPCDMDocumentationViewer(MDXSearchTool):
    def __init__(self, mdx=os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "OMOP_CDM_v5.4.md")):
        super().__init__(
            mdx=mdx,
            config=dict(
                llm=dict(
                    provider="ollama",
                    config=dict(
                        model="mistral",
                        # Optional parameters can be included here.
                        # temperature=0.5,
                        # top_p=1,
                        # stream=True,
                    ),
                ),
                embedder=dict(
                    provider="huggingface",
                    config=dict(
                        model="BAAI/bge-large-en-v1.5",
                        # Optional title for the embeddings can be added here.
                        # title="Embeddings",
                    ),
                ),
            )
        )
        self.name = "OMOP CDM Documentation Search"
        self.description = "Searches inside the general OMOP CDM documentation using the argument search_query."


class SimilarExamplesRetrieverToolInput(BaseModel):
    query: str = Field(..., description="The natural language query to find similar SQL examples")

class SimilarExamplesRetrieverTool(BaseTool):
    name: str = "Similar Examples Retriever"
    description: str = "Retrieves similar SQL examples from a FAISS index."
    args_schema: Type[BaseModel] = SimilarExamplesRetrieverToolInput

    def _run(self, query: str) -> str:
        try:
            response = requests.post(
                "http://localhost:5001/link",
                json={"query": query},
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            return f"API request failed: {e}"


if __name__ == "__main__":
    tool = SimilarExamplesRetrieverTool()

    print(tool.run("Number of patients"))