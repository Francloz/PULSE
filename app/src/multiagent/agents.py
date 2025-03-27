from typing import Any, List

from crewai import Agent, Task, Crew, Process

"""
Notes on agents from docs.crewai.com

Goal: The Agent’s Purpose and Motivation
The goal directs the agent’s efforts and shapes their decision-making process. Effective goals should:

Be clear and outcome-focused: Define what the agent is trying to achieve
Emphasize quality standards: Include expectations about the quality of work
Incorporate success criteria: Help the agent understand what “good” looks like


Backstory: The Agent’s Experience and Perspective
The backstory gives depth to the agent, influencing how they approach problems and interact with others. Good backstories:

Establish expertise and experience: Explain how the agent gained their skills
Define working style and values: Describe how the agent approaches their work
Create a cohesive persona: Ensure all elements of the backstory align with the role and goal

Specialists Over Generalists
Agents perform significantly better when given specialized roles rather than general ones. A highly focused agent delivers more precise, relevant outputs:
"""

class InformationCompletionist(Agent):
    def __init__(self, backstory=None):
        if backstory is None:
            backstory = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                         "data model for statistical analysis, when a clinician requests data you know what information"
                         "is incomplete for the queries they asked for in a methodical and careful manner in order to "
                         "preemptively solve ambiguities that might arise when crafting queries for the database")
        super().__init__(role="Request any information required to translate medical queries for cohort analysis to structured queries",
                         goal="Obtain clear and concise information that complements a stated data query to allow "
                              "crafting correct and precise structured queries on OMOP CDM"
                              " unambiguous and correct",
                         backstory=backstory,
                         allow_delegation=False)


class InformationInquiryCrafter(Agent):
    def __init__(self, backstory=None):
        if backstory is None:
            backstory = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                         "data model for statistical analysis, when a clinician requests data with complementary information"
                         "to resolve ambiguities you know how to ensemble it together to create a clear and structured"
                         "inquiry that will be translated to SQL")
        super().__init__(role="Data Engineer with expertise in hospital data integration and OMOP CDM databases",
                         goal="Craft natural language queries for OMOP databases that are clear and unambiguous",
                         backstory=backstory,
                         allow_delegation=False)

class QueryPlanner(Agent):
    def __init__(self, backstory=None):
        if backstory is None:
            backstory = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                         "data model for statistical analysis, when a colleague requests a SQL query for a data inquiry"
                         "in OMOP CDM databases, you know how to create step by step instructions on how to build the query"
                         "in a clear and structured manner")
        super().__init__(role="Data Engineer with expertise in hospital data integration and OMOP CDM databases",
                         goal="Craft detailed plans to write SQL queries for OMOP databases",
                         backstory=backstory)


class QueryDecomposer(Agent):
    def __init__(self, backstory=None):
        if backstory is None:
            backstory = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                         "data model for statistical analysis, when a colleague gives a detailed implementation plan for"
                         " a SQL query in OMOP CDM databases, you know how to subdivide it into step by step SQL queries "
                         "to solve the problem recursively")
        super().__init__(role="Data Engineer with expertise in hospital data integration and OMOP CDM databases",
                         goal="Craft detailed plans to write SQL queries for OMOP databases",
                         backstory=backstory)


class DatabaseChecker(Agent):
    def __init__(self, backstory: str=None):
        if backstory is None:
            backstory = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                         "data model for statistical analysis, when a colleague gives a detailed implementation plan for"
                         " a SQL query in OMOP CDM databases, you know how to subdivide it into step by step SQL queries "
                         "to solve the problem recursively")
        super().__init__(role="Data Engineer with expertise in hospital data integration and OMOP CDM databases",
                         goal="Craft detailed plans to write SQL queries for OMOP databases",
                         backstory=backstory,
                         tools=[])

class Text2SQLCrew(Crew):
    def __init__(self, agents: List[Agent], tasks: List[Task], /, **data: Any):
        super().__init__(agents=agents,
                         tasks=tasks,
                         process=Process.sequential,
                         **data)

class CompleteQuery(Task):
    def __init__(self, agent, /, **data: Any):
        super().__init__(description="Request information necessary to correctly translate the natural language query"
                                     "into a SQL query for an OMOP database",
                         expected_output="Clear information request",
                         agent=agent,
                         **data)


def get_text2sql_crew(has_completionist=False):
    agents = []
    tasks = []

    if has_completionist:
        completionist = InformationCompletionist()
        completionist_task = CompleteQuery(completionist)
        agents.append(completionist)
        tasks.append(completionist_task)

    return Crew(agents=agents, tasks=tasks, process=Process.sequential)