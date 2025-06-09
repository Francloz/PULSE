import os

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from crewai_tools.tools.mdx_seach_tool.mdx_search_tool import MDXSearchTool

from tools import LinkMentionsTool, SearchEngineTool, path_to_omopcdm_doct  # Only needed by mapper_agent

@CrewBase
class MapperCrew():
    """OMOP Entity Tagging and Mapping Crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    agents: List[BaseAgent]
    tasks: List[Task]

    llm = LLM(
        model="ollama/qwen3:30b-a3b",
        # model="ollama/qwen2.5:14b-instruct",
        # model="ollama/mistral-small:24b-instruct-2501-q4_K_M",
        base_url="http://localhost:11434",
    )

    @agent
    def abbreviation_solver_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['abbreviation_solver_agent'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
            tools=[SearchEngineTool()]
        )

    @agent
    def tagger_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['tagger_agent'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
            tools=[SearchEngineTool(), MDXSearchTool(mdx=path_to_omopcdm_doct,
                                     config=dict(
                                         llm= dict(
                                            provider="ollama",
                                            config=dict(
                                                model="qwen3:30b-a3b",
                                                base_url="http://localhost:11434"
                                            )
                                        ),
                                         embedder=dict(
                                             provider="huggingface",
                                             config=dict(
                                                 model="BAAI/bge-large-en-v1.5",
                                             ),
                                         ),
                                     )
                                     )]
        )

    @agent
    def mapper_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['mapper_agent'],  # type: ignore[index]
            verbose=True,
            tools=[LinkMentionsTool()],
            llm=self.llm,
        )

    @agent
    def validator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['validator_agent'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
        )

    def boss(self) -> Agent:
        return Agent(
            config=self.agents_config['boss'],  # type: ignore[index]
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )

    @task
    def abbreviation_solver_task(self) -> Task:
        return Task(
            config=self.tasks_config['abbreviation_solver_task'],  # type: ignore[index]
        )

    @task
    def tag_task(self) -> Task:
        return Task(
            config=self.tasks_config['tag_task'],  # type: ignore[index]
        )

    @task
    def map_task(self) -> Task:
        return Task(
            config=self.tasks_config['map_task'],  # type: ignore[index]
        )

    @task
    def validate_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MapperCrew for OMOP entity tagging and mapping"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential,
            # manager_agent=self.boss(),
            # manager_llm=self.llm,
            # process=Process.hierarchical,  # You may use Process.hierarchical with boss as manager
        )