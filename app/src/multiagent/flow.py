import csv
import difflib
import io
import random
import sqlite3
import string
import tempfile

import sqlglot
from crewai.flow.flow import Flow, listen, start, or_
from pydantic import BaseModel, Field
from enum import IntEnum
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from app.src import config
from multiagent.model import get_llm
import re
import json
import ast
from sqlglot import parse_one, exp
from sqlglot.optimizer.qualify import qualify
from faker import Faker
import faker
from synthetic_db_utils import database2str, get_necessary_tables_and_columns, create_synthetic_database
from prompts import *
from utils import ChatState


def extract_qa_pairs(text_data, alt="reason"):
    """
    Parses a string that contains a list of dictionaries (like Python literals),
    even if there is preceding text before the list structure.
    Extracts question-answer pairs.

    :param alt:
    :param text_data: A string potentially containing introductory text followed by the data structure.
    :return: A list of tuples, where each tuple is (question, answer).
            Returns an empty list if parsing fails or no valid list structure is found.
    """
    qa_pairs = []

    try:
        start_index = text_data.find('[')
        # Use rfind to get the *last* closing bracket, assuming the main list is the outer structure
        end_index = text_data.rfind(']')

        if start_index == -1 or end_index == -1 or end_index <= start_index:
            print("Error: Could not find valid list structure ([...]) in the text.")
            return []

        # Extract the substring that contains the list
        list_substring = text_data[start_index: end_index + 1]

    except Exception as e:
        print(f"Error finding list structure: {e}")
        return []

    try:
        # ast.literal_eval safely parses Python literals from the substring
        list_substring = list_substring.replace('’', '\'')
        list_substring = list_substring.replace('‘', '\'')
        list_substring = list_substring.replace('”', '\"')
        parsed_data = ast.literal_eval(list_substring)
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing with ast.literal_eval on substring: {e}")
        return []

    # Check if the parsed data is a list
    if not isinstance(parsed_data, list):
        print("Parsed data is not a list.")
        return []

    # Iterate through the list and extract Q&A
    for item in parsed_data:
        if isinstance(item, dict):
            question = item.get('question')
            # Treat 'reason' as the 'answer' based on the input structure
            answer = item.get(alt)

            if question and answer:
                qa_pairs.append((question, answer))
            else:
                print(f"Skipping item, missing 'question' or '{alt}': {item}")
        else:
            print(f"Skipping item, not a dictionary: {item}")

    return qa_pairs


class DatabaseConfig(BaseModel):
    """
    This class represents a unique database.

    Attributes:
        name (str): Name of the database. In principle only for debug purposes.
        uri (str): URI of the database connection used with SQL Alchemy.
    """
    name: str
    uri: str


class ExecutionEnum(IntEnum):
    """
    This class represents an enumeration of types of possible outcomes of a SQL code execution.
    """
    error = -1  # Indicates an execution error
    valid = 0  # Indicates a valid execution


class ExecutionResult(BaseModel):
    """
    This class represents the execution result of a SQL code execution.

    Attributes:
        status (ExecutionEnum): Type of outcome
        result (str): Returned result TODO Consider changing this type from str to an alternative
    """
    status: ExecutionEnum
    result: str


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
        random_databases (List[DatabaseConfig]): random tables to test the queries on
        similar_examples (List[Tuple[str, str]]): similar examples for few-shot prompting
        temp_views (List[str]): temporary views that can be assumed to contain the DB TODO refine this further
        consistent_sql (str): the most consistent sql query translation
    """
    query: str = ""
    sql_alternatives: List[str] = field(default_factory=list)
    exec_results: List[ExecutionResult] = field(default_factory=list)
    expected_results: List[str] = field(default_factory=list)
    valid_sql_alternatives: List[str] = field(default_factory=list)
    random_databases: List[DatabaseConfig] = field(default_factory=list)
    similar_examples: List[Tuple[str, str]] = field(default_factory=list)
    temp_views: List[str] = field(default_factory=list)
    consistent_sql: str = ""


class TaskState(BaseModel):
    """
    This class represents the current state of the process in from NL query to SQL query.

    Attributes:
        user_name (str): Name of the user requesting this task
        language (str): language of the query
        initial_inquiry (str): initial NL query
        completed_inquiry (str): final result of the query
        tables_and_columns (Dict[str, str]): pairs of table and column that are used for this query
        decomposed_queries (List[QueryState]): decomposition of the es
        step (int): current step, equivalent to the number of sub-queries translated
        total_sql (str): final SQL translation of the NL query on OMOP CDM
    """
    user_name: str = ""
    language: str = "English"
    initial_inquiry: str = ""
    completed_inquiry: str = ""

    tables_and_columns: Dict[str, str] = field(default_factory=dict)
    decomposed_queries: List[QueryState] = field(default_factory=list)
    step: int = 0
    total_sql: str = ""


ChatState.model_rebuild()


class Text2SQLFlow(Flow[TaskState]):
    """
    Flow of the task of NL to SQL query.
    """

    def __init__(self, username: str, initial_inquiry: str, debug: bool = False, **kwargs: Any):
        """
        Initializes the flow with the necessary data that is specific to this flow.
        :param username: name of the user, to refer to them by name
        :param initial_inquiry: initial natural language inquiry sent by the user
        :param debug: whether to show debug prints
        :param kwargs: other kwargs of CrewAI's Flow
        """
        super().__init__(**kwargs)
        self.state.user_name = username
        self.state.initial_inquiry = initial_inquiry
        self.debug = debug

    @staticmethod
    def get_documentation_on(text: str) -> str:
        pass

    @start()
    def initialize_data(self) -> str:
        """
        Initialization of the flow.
        :return: string of the result
        """

        return "Initialized"

    @listen(initialize_data)
    def complete_query(self):
        """
        Attempts to complete the NL query with information required. A LLM may connect to the user through text
        requests to do this.

        :return: string of the results
        """
        extra_info = []

        # Get the doubts of the LLM
        llm = get_llm()
        prompt = DOUBT_DETECTION_PROMPT.format(initial_inquiry=self.state.initial_inquiry)
        response = llm.call(
            prompt
        )
        q2r = extract_qa_pairs(response)  # questions and reasons

        if self.debug:
            print(prompt)
            print(response)
            print(q2r)

        if len(q2r) == 0:  # If there are no questions, just continue
            self.state.completed_inquiry = self.state.initial_inquiry
        else:  # If there are questions, solve the ambiguities
            # TODO Change this part to ask user for the information ----------------------------------------------------
            #  This is a placeholder for actually asking the user.
            output_lines = []
            for idx, (q, a) in enumerate(q2r, start=1):
                output_lines.append(f"{idx}. Question: {q}\n   Reason: {a}")
            q2r_text = "\n".join(output_lines)
            llm = get_llm()
            prompt_self_answer = (
                "You are a seasoned data engineer with deep experience helping hospitals migrate to the OMOP Common Data Model "
                "for accurate and efficient statistical analysis. You understand clinical data requests deeply and interpret them "
                "with confidence. When ambiguity arises, you do not hesitate—you make clear, reasonable assumptions and proceed. "
                "You always favor simplicity and clarity, and you respond with final decisions—not suggestions. "
                "Avoid using uncertain language like 'could', 'might', 'if this', or 'we could'. Always choose a single course of action. "
                "Be specific, direct, and final in your answers."
                f"\n----------\n"
                f"For this query for OMOP CDM DB {self.state.initial_inquiry}. Resolve these questions executi:"
                f"\n{q2r_text}"
                f"\nAnswer it with JSON format [{{'question': question, 'answer': answer}},...]")

            response = llm.call(
                prompt_self_answer
            )
            q2a = [{'question': q, 'answer': a} for q, a in extract_qa_pairs(response, alt="answer")]
            extra_info += q2a

            if self.debug:
                print(prompt)
                print(response)
                print(extra_info)
            # TODO END -------------------------------------------------------------------------------------------------

            # Agglomerate the questions and answers for the query completionist
            if len(extra_info) == 0:
                q2r_text = "None."
            else:
                output_lines = []
                for idx, d in enumerate(extra_info, start=1):
                    output_lines.append(f"{idx}. Question: {d['question']}\n   Answer: {d['answer']}")
                q2r_text = "\n".join(output_lines)

            # Request the query be rewritten so that it is unambiguous
            llm = get_llm()
            prompt = QUERY_REWRITE_PROMPT.format(initial_inquiry=self.state.initial_inquiry, information=q2r_text)
            response = llm.call(
                prompt
            )

            # Extract the natural language query
            match = re.search(r'<<\s*Rewritten query:\s*(.*?)\s*>>', response)
            if match:
                extracted_text = match.group(1)
            else:
                extracted_text = "Error"

            if self.debug:
                print(prompt)
                print(response)
                print(f"The reformulated query is: {extracted_text}")

            self.state.completed_inquiry = extracted_text

        if self.state.completed_inquiry == "Error":
            return "Error"
        else:
            return "Inquiry completed"

    @listen(complete_query)
    def decompose_query(self):
        """
        Attempts to decompose the query into several sub-queries that can be translated one by one.

        :return: string of the results
        """
        llm = get_llm()
        prompt = DECOMPOSITION_PROMPT.format(initial_inquiry=self.state.completed_inquiry)
        response = llm.call(
            prompt
        )

        steps = re.findall(r'^\d+:\s*(.+)$', response, flags=re.MULTILINE)

        if self.debug:
            print(prompt)
            print(response)
            print(steps)
        self.state.decomposed_queries = []
        for step in steps:
            subquery = QueryState()
            subquery.query = step
            self.state.decomposed_queries.append(subquery)
        return "Query decomposed"

    @listen(or_(decompose_query, "Alternatives consolidated"))
    def prepare_alternatives(self):
        """
        Attempts to prepare several SQL alternatives and a batch of synthetic databases that can be used to test the
        queries on.

        :return: string of the results
        """
        if self.state.step == len(self.state.decomposed_queries):
            return "All steps finished"

        current_query = self.state.decomposed_queries[self.state.step].query

        alternatives = self.state.decomposed_queries[self.state.step].sql_alternatives
        prompt = TRANSLATION_PROMPT.format(query=current_query, views="None")

        for alt in range(config.NUM_CONSISTENCY_REPLICATES):
            llm = get_llm(temperature=0.05)
            response = llm.call(prompt)

            match = re.search(r"```SQL\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
            sql_code = None
            if match:
                sql_code = match.group(1)
                alternatives.append(sql_code)

            if self.debug:
                print(prompt)
                print("Extracted SQL code:")
                print(sql_code)

        tables = get_necessary_tables_and_columns(self.state.decomposed_queries[self.state.step].sql_alternatives)

        databases = self.state.decomposed_queries[self.state.step].random_databases
        expected_results = self.state.decomposed_queries[self.state.step].expected_results

        for db_idx in range(config.NUM_SYNTHETIC_DB):
            database = create_synthetic_database(tables)
            db_conf = DatabaseConfig(uri=database, name=str(db_idx))
            databases.append(db_conf)

        for database in databases:
            database_str = database2str(database.uri)

            llm = get_llm()
            prompt = SIMULATE_SQL_ON_DB_PROMPT.format(database=database_str, query=current_query)
            result_str = llm.call(prompt)
            result = result_str.split("RESULT:")[1]
            result = result.replace("csv", "").replace("`", "").strip()

            expected_results.append(result)

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

    @listen("All steps finished")
    def compose(self):
        """
        Composes the query using the sub-queries.

        :return: string of result
        """
        return "Final query composed"

    @listen(compose)
    def validate_final_query(self):
        """
        Executes the final query and gets the result.

        :return: string of result
        """
        return self.state.total_sql

    @listen("Error")
    def error(self):
        """
        Function that processes an error in the text to SQL translation.

        :return: string of result
        """
        # TODO Tell the user the error
        pass


if __name__ == "__main__":
    flow_instance = Text2SQLFlow(username="Paco", initial_inquiry="Average age of all patients", debug=True)
    flow_instance.kickoff()
