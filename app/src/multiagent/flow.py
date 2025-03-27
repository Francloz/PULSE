from crewai.flow.flow import Flow, listen, start, or_
from pydantic import BaseModel, Field
from enum import IntEnum
from typing import List, Dict, Optional, Tuple

from app.src import config


class DatabaseConfig(BaseModel):
    name: str
    uri: str

class ExecutionEnum(IntEnum):
    error = -1
    valid = 0

class ExecutionResult(BaseModel):
    status: ExecutionEnum
    result: str

class QueryState(BaseModel):
    query: str
    temp_views: List[str] = []
    sql_alternatives: List[str]
    exec_results: List[ExecutionResult]
    expected_results: List[str]
    valid_sql_alternatives: List[str]
    random_tables: List[DatabaseConfig] = []
    similar_examples: List[Tuple[str, str]] = []
    consistent_sql: str = ""

class TaskState(BaseModel):
    user_name: str = ""
    language: str = "English"
    initial_inquiry: str = ""
    in_completion_inquiry: str = ""
    completed_inquiry: str = ""

    tables_and_columns: Dict[str, str] = ""
    decomposed_queries: List[QueryState] = []
    step:int = 0
    total_sql:str = ""


class Text2SQLFlow(Flow[TaskState]):
    @start()
    def initialize_data(self, username, initial_inquiry):
        self.state.user_name = username
        self.state.initial_inquiry = initial_inquiry
        return "Initialized"

    @listen(initialize_data)
    def complete_query(self):
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
        # TODO Ask the LLM to decompose the SQL query into steps
        return "Query decomposed"

    @listen(decompose_query)
    def prepare_alternatives(self):
        # TODO Ask the LLM to generate SQL translations
        # TODO Generate simple synthetic databases
        # TODO Ask the LLM to generate the expected results of the query on the synthetic databases
        return "Alternatives prepared"

    @listen(prepare_alternatives)
    def test_and_consolidate(self):
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
        return "Alternatives prepared"

    @listen("Error")
    def error(self):
        pass # TODO Tell the user the error





