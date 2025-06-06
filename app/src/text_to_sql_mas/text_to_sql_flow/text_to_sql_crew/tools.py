import os
from typing import Type

import requests
from crewai_tools.tools.mdx_seach_tool.mdx_search_tool import MDXSearchTool
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class SchemaLinkingToolInput(BaseModel):
    tables: list[str] = Field(..., description="List of table names to analyze")
    columns: list[str] = Field(..., description="List of column names to include")

class SchemaLinkingTool(BaseTool):
    name: str = "Schema Linking Tool"
    description: str = "Generates a concise schema description with example values from a PostgreSQL database."
    args_schema: Type[BaseModel] = SchemaLinkingToolInput

    def _run(self, tables: list[str], columns: list[str], query: str) -> str:
        # Placeholder logic
        return f"Linked schema for query: '{query}' using tables: {tables} and columns: {columns}"

path_to_omopcdm_doct = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge", "OMOP_CDM_v5.4.md")
# Initialize the tool with a specific MDX file path for an exclusive search within that document


class SimilarExamplesRetrieverToolInput(BaseModel):
    query: str = Field(..., description="The natural language query to find similar SQL examples")

class SimilarExamplesRetrieverTool(BaseTool):
    name: str = "Similar Examples Retriever"
    description: str = "Retrieves top 3 similar SQL examples from a FAISS index."
    args_schema: Type[BaseModel] = SimilarExamplesRetrieverToolInput

    def _run(self, queries: list[str]) -> str:
        try:
            response = requests.post(
                "http://localhost:5001/sql_examples",
                json={"queries": queries},
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            return f"API request failed: {e}"
