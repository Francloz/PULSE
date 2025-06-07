import os
import sys
import traceback
from typing import Type, Tuple
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests


path_to_omopcdm_doct = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge", "OMOP_CDM_v5.4.md")

class LinkMentionsInput(BaseModel):
    mentions: list[Tuple[str, str]] = Field(
        ...,
        description=(
            "List of biomedical mentions and their categories. "
            "Each item **must** be a tuple with two elements: "
            "(entity: str, category: str). "
            "Example: [('Hispanic', 'RACE'), ('male', 'GENDER'), ('type 2 diabetes', 'CONDITION')]"
        )
    )
class LinkMentionsTool(BaseTool):
    name: str = "LinkMentionsTool"
    description: str = (
        "Links biomedical entities with their associated categories to standardized concept IDs. "
        "Input must be a list of (entity, category) pairs."
    )
    args_schema: Type[BaseModel] = LinkMentionsInput

    def _run(self, mentions: list[Tuple[str, str]]) -> str:
        try:
            mentions = {"mentions": [{"text": mention[0], "tag": mention[1]} for mention in mentions]}
            response = requests.post(
                "http://localhost:5000/link",
                json=mentions,
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(mentions, file=sys.stderr)
            traceback.print_exc()
            return f"API request failed: {e}"


from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults


class SearchEngineToolInput(BaseModel):
    query: str = Field(..., description="Query to find relevant results")

class SearchEngineTool(BaseTool):
    name: str = "Search Engine"
    description: str = "Search the web using a search engine."
    args_schema : Type[BaseModel] = SearchEngineToolInput

    def _run(self, query: str) -> str:
        search_engine = DuckDuckGoSearchResults()
        response = search_engine.invoke(query)
        return response