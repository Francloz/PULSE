from crewai_tools import MDXSearchTool


import os
path_to_omopcdm_doct = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge", "OMOP_CDM_v5.4.md")

class OMOPCDMDocumentationViewer(MDXSearchTool):
    def __init__(self, mdx=path_to_omopcdm_doct):
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



