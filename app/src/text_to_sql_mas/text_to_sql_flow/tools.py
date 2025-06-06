from crewai_tools import MDXSearchTool


import os
path_to_omopcdm_doct = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge", "OMOP_CDM_v5.4.md")
# Initialize the tool with a specific MDX file path for an exclusive search within that document
documentation_viewer = MDXSearchTool(mdx=path_to_omopcdm_doct)