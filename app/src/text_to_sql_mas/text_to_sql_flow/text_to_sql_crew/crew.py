from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from crewai_tools.tools.mdx_seach_tool.mdx_search_tool import MDXSearchTool

from tools import SchemaLinkingTool, SimilarExamplesRetrieverTool, path_to_omopcdm_doct

@CrewBase
class SQLPlannerCrew():
    """Multi-Agent SQL Planning Crew"""
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
    def schema_linker_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['schema_linker_agent'],  # type: ignore[index]
            verbose=True,
            tools=[# SchemaLinkingTool(),
                   MDXSearchTool(mdx=path_to_omopcdm_doct,
                                 config=dict(
                                     llm=dict(
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
                                 )
                   ],
            llm=self.llm,
        )

    @agent
    def sql_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_planner_agent'],  # type: ignore[index]
            verbose=True,
            tools=[MDXSearchTool(mdx=path_to_omopcdm_doct,
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
                                     ),
                   SimilarExamplesRetrieverTool()],
            llm=self.llm,
        )

    @agent
    def sql_expert_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_expert_agent'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
        )

    def boss_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['boss'],  # type: ignore[index]
            verbose=True,
            llm=self.llm,
        )

    @task
    def schema_linking_task(self) -> Task:
        return Task(
            config=self.tasks_config['schema_linking_task'],  # type: ignore[index]
        )

    @task
    def planning_task(self) -> Task:
        return Task(
            config=self.tasks_config['planning_task'],  # type: ignore[index]
        )


    @task
    def sql_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['sql_generation_task'],  # type: ignore[index]
        )

    @task
    def argument_substitution_task(self) -> Task:
        return Task(
            config=self.tasks_config['argument_substitution_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            manager_agent=self.boss_agent(),  # SQL Planner acts as the coordinator
            manager_llm=self.llm,
            process=Process.hierarchical,
            output_log_file=True  # Saves logs to 'logs.txt'
        )
