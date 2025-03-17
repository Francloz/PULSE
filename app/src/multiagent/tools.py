import logging
from typing import Type
import requests
from crewai.tools import BaseTool, tool
from crewai_tools import RagTool
from pydantic import BaseModel, Field
import psycopg2

from ..config import OMOP_DB_PARAMS, OMOP_DOCS_PATH

class MyToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class ColumnExamplesOMOP(BaseTool):
    name: str = "Name of my tool"
    description: str = "Given a list of pairs of table:column in the OMOP database, it returns examples found in each column"
    args_schema: Type[BaseModel] = MyToolInput
    limit: int = 10

    @staticmethod
    def get_table_col_pairs(text):
        return []

    def _run(self, argument: str) -> str:
        total_result = ""
        for table, column in self.get_table_col_pairs(argument):
            query = f"SELECT DISTINCT {column} FROM {table} LIMIT {self.limit}"
            try:
                # Using a context manager to ensure the connection is closed automatically
                with psycopg2.connect(**OMOP_DB_PARAMS) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query)
                        result = cur.fetchall()  # adjust based on your query type
                        result = [elem[0] for elem in result]
                        total_result += f"Examples of {column} in {table}: {str(result)}\n"
            except Exception as e:
                logging.error(f"Error querying {column} of {table}", exc_info=True)
                return f"Error querying {column} of {table}"
        return total_result[:-1]

@tool
def recheck_omop_tool():
    rag_tool = RagTool()
    rag_tool.add(data_type="web_page", path=OMOP_DOCS_PATH)
    return rag_tool


