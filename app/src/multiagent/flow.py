from crewai.flow.flow import Flow, listen, start, or_
from pydantic import BaseModel, Field
from enum import IntEnum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from app.src import config

@dataclass
class DatabaseConfig(BaseModel):
    """
    This class represents a unique database.

    Attributes:
        name (str): Name of the database. In principle only for debug purposes.
        uri (str): URI of the database connection used with SQL Alchemy.
    """
    name: str
    uri: str

@dataclass
class ExecutionEnum(IntEnum):
    """
    This class represents an enumeration of types of possible outcomes of a SQL code execution.
    """
    error = -1 # Indicates an execution error
    valid = 0 # Indicates a valid execution

@dataclass
class ExecutionResult(BaseModel):
    """
    This class represents the execution result of a SQL code execution.

    Attributes:
        status (ExecutionEnum): Type of outcome
        result (str): Returned result TODO Consider changing this type from str to an alternative
    """
    status: ExecutionEnum
    result: str

@dataclass
class QueryState(BaseModel):
    """
    This class represents the state of a simple NL query to SQL translation. It goes from creating
    several sql alternatives for it, executions of these queries, selection of valid ones, creation of
    tables to test the results of them, and selection of the most consistent one.

    Attributes:
        query (str): original NL query
        sql_alternatives (List[str]): translation options
        exec_results (List[ExecutionResult]): execution results
        expected_results (List[str]): expected results
        valid_sql_alternatives (List[str]): valid sql alternatives
        random_tables (List[DatabaseConfig]): random tables to test the queries on
        similar_examples (List[Tuple[str, str]]): similar examples for few-shot prompting
        temp_views (List[str]): temporary views that can be assumed to contain the DB TODO refine this further
        consistent_sql (str): the most consistent sql query translation
    """
    query: str
    sql_alternatives: List[str]
    exec_results: List[ExecutionResult]
    expected_results: List[str]
    valid_sql_alternatives: List[str]
    random_tables: List[DatabaseConfig] = field(default_factory=list)
    similar_examples: List[Tuple[str, str]] = field(default_factory=list)
    temp_views: List[str] = field(default_factory=list)
    consistent_sql: str = ""

@dataclass
class TaskState(BaseModel):
    """
    This class represents the current state of the process in from NL query to SQL query.

    Attributes:
        user_name (str): Name of the user requesting this task
        language (str): language of the query
        initial_inquiry (str): initial NL query
        in_completion_inquiry (str): current state of the query, it may include incomplete steps
        completed_inquiry (str): final result of the query
        tables_and_columns (Dict[str, str]): pairs of table and column that are used for this query
        decomposed_queries (List[QueryState]): decomposition of the es
        step (int): current step, equivalent to the number of sub-queries translated
        total_sql (str): final SQL translation of the NL query on OMOP CDM
    """
    user_name: str = ""
    language: str = "English"
    initial_inquiry: str = ""
    in_completion_inquiry: str = ""
    completed_inquiry: str = ""

    tables_and_columns: Dict[str, str] = ""
    decomposed_queries: List[QueryState] = field(default_factory=list)
    step:int = 0
    total_sql:str = ""


class Text2SQLFlow(Flow[TaskState]):
    """
    Flow of the task of NL to SQL query.
    """
    @start()
    def initialize_data(self, username, initial_inquiry):
        """
        Initialization of the flow. It requires the username of the requester and the initial natural language inquiry.

        :param username: Username of the requester
        :param initial_inquiry: Initial NL query
        :return: string of the result
        """
        self.state.user_name = username
        self.state.initial_inquiry = initial_inquiry
        return "Initialized"

    @listen(initialize_data)
    def complete_query(self):
        """
        Attempts to complete the NL query with information required. A LLM may connect to the user through text
        requests to do this.

        :return: string of the results
        """
        is_complete = False
        while not is_complete:
            # TODO Ask the LLM if the info is enough
            # TODO Ask the LLM what information is needed
            # TODO Ask user for the information
            # TODO Add information to the inquiry
            pass
        return "Inquiry completed"

    @listen(complete_query)
    def decompose_query(self):
        """
        Attempts to decompose the query into several sub-queries that can be translated one by one.

        :return: string of the results
        """
        # TODO Ask the LLM to decompose the SQL query into steps
        return "Query decomposed"

    @listen(decompose_query)
    def prepare_alternatives(self):
        """
        Attempts to prepare several SQL alternatives and a batch of synthetic databases that can be used to test the
        queries on.

        :return: string of the results
        """
        # TODO Ask the LLM to generate SQL translations
        # TODO Generate simple synthetic databases
        # TODO Ask the LLM to generate the expected results of the query on the synthetic databases
        return "Alternatives prepared"

    @listen(prepare_alternatives)
    def test_and_consolidate(self):
        """
        Goes from sub-query to sub-query testing them to see how they do on the synthetic databases and selects the best
        alternative.

        :return: string of the result
        """
        assert config.ON_SQL_TEST_FAILURE == "SKIP", "Currently, the only accepted action taken if a SQL alternative's " \
                                                     "test fails is skipping that alternative"

        for sub_query in self.state.decomposed_queries:
            # TODO Run the queries on the synthetic databases
            # TODO Compare the results to the expected ones
            # TODO Filter the erroneous queries

            idx = []
            for i, test in enumerate(sub_query.exec_results):
                if test.status == ExecutionEnum.valid:
                    idx.append(i)
            sub_query.exec_results = [sub_query.exec_results[i] for i in idx]
            sub_query.sql_alternatives = [sub_query.sql_alternatives[i] for i in idx]
            if len(sub_query.sql_alternatives) == 0:
                return "Error"

            # TODO Select best

            self.state.step += 1
        return "Alternatives consolidated"

    @listen("Alternatives consolidated")
    def compose(self):
        """
        Composes the query using the sub-queries.

        :return: string of result
        """
        return "Final query composed"

    @listen(compose)
    def execute_final_query(self):
        """
        Executes the final query and gets the result.

        :return: string of result
        """
        return "Last result"

    @listen("Error")
    def error(self):
        """
        Function that processes an error in the text to SQL translation.

        :return: string of result
        """
        pass # TODO Tell the user the error





