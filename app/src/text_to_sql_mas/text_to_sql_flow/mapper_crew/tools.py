import json
import os
import sys
import traceback
from typing import Type, Tuple, Union
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests


path_to_omopcdm_doct = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge", "OMOP_CDM_v5.4.md")

class LinkMentionsInput(BaseModel):
    mentions: Union[list[Tuple[str, str]], list[str]] = Field(
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

    def _run(self, mentions: Union[list[Tuple[str, str]], list[str]]) -> str:
        try:
            if all(isinstance(item, str) for item in mentions):
                assert len(mentions) % 2 == 0, "Always give both the entity and the category."
                mentions =  [(mentions[i], mentions[i + 1]) for i in range(0, len(mentions), 2)]

            mentions = {"mentions": [{"text": mention[0], "tag": mention[1]} for mention in mentions]}
            response = requests.post(
                "http://localhost:5000/link",
                json=mentions,
                timeout=10
            )
            response.raise_for_status()

            simplified = []
            for item in response.json():
                mention = item["mention"]
                mappings = item["mappings"]

                if not mappings:
                    continue  # Skip if no mappings

                top_mapping = mappings[0]  # Take only the first mapping

                simplified.append({
                    "text": mention["text"],
                    "tag": mention["tag"],
                    "concept_id": top_mapping["concept_id"],
                    "concept_name": top_mapping["concept_name"],
                    "concept_class": top_mapping["concept_class_id"]
                })

            return json.dumps(simplified, indent=4)
        except requests.RequestException as e:
            print(mentions, file=sys.stderr)
            traceback.print_exc()
            return f"API request failed: {e}"


from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults


class SearchEngineToolInput(BaseModel):
    query: str = Field(..., description="Concept or term to define")

class SearchEngineTool(BaseTool):
    name: str = "Search Engine"
    description: str = "Define a concept using the search engine."
    args_schema : Type[BaseModel] = SearchEngineToolInput

    def _run(self, query: str) -> str:
        search_engine = DuckDuckGoSearchResults(num_results=1)
        response = search_engine.invoke(f"In medicine, what is {query}?")
        return response