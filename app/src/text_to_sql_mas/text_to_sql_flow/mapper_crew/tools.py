from typing import Type, Tuple
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests

class LinkMentionsInput(BaseModel):
    mentions: list[Tuple[str, str]] = Field(..., description="List of biomedical mentions to link and their categories")

class LinkMentionsTool(BaseTool):
    name: str = "LinkMentionsTool"
    description: str = "Links biomedical mentions with a category to concepts using the BioBERT entity linker API"
    args_schema: Type[BaseModel] = LinkMentionsInput

    def _run(self, mentions: list[Tuple[str, str]]) -> str:
        try:
            response = requests.post(
                "http://localhost:5000/link",
                json={"mentions": mentions},
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
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