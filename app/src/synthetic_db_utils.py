import csv
import difflib
import io
import random
import sqlite3
import tempfile
import sqlglot
from typing import List, Dict, Optional, Tuple, Any
from app.src import config
import re
import ast
from sqlglot import parse_one, exp
from sqlglot.optimizer.qualify import qualify
from faker import Faker


# noinspection SqlNoDataSourceInspection
def create_synthetic_database(tables: Dict[str, List[str]], add_non_nullable: bool = True) -> str:
    """
    Create a synthetic database of OMOP CDM restricted to only the tables in 'tables' and the columns
    :param add_non_nullable: whether to add the columns that are not nullable of the OMOP CDM DB to the synthetic db
    :param tables: Map from tables to the columns inside them that are used
    :return: database connection configuration
    """
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db', dir=config.DATA_DIR).name
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    data = {}
    for table, cols in tables.items():
        real_schema = config.OMOP_SCHEMA[table]
        data[table] = {}

        extra_cols = [other_col for other_col, col_config in config.OMOP_SCHEMA[table].items() if other_col not in cols
                      and not col_config.endswith("NOT NULL")]

        for col in cols + extra_cols:
            column_settings = real_schema[col].split(" ")

            _type, nullable = column_settings[0], len(column_settings) < 3

            data[table][col] = []
            if col.endswith("_id"):
                if col.startswith(table):
                    data[table][col] = [i + 1 for i in range(config.SZ_SYNTHETIC_DB)]
                else:
                    data[table][col] = [random.randint(1, config.SZ_SYNTHETIC_DB) for _ in
                                        range(config.SZ_SYNTHETIC_DB)]

            elif nullable and random.random() < config.PROB_NULL_SYNTHETIC_DB:
                data[table][col].append(None)

            elif _type == "integer":
                # TODO Create random integers that are not completely random to not confuse the LLM
                data[table][col] = [random.randint(1, 100) for _ in range(config.SZ_SYNTHETIC_DB)]

            elif _type == "float":
                # TODO Create random floats that are not completely random to not confuse the LLM
                data[table][col] = [random.random() * 64 for _ in range(config.SZ_SYNTHETIC_DB)]

            elif _type.startswith("varchar("):
                numbers = re.findall(r'\d+', _type)
                if len(numbers) > 0:
                    length = int(numbers[0])
                else:
                    length = 255  # default length

                # TODO Either a static method to get strings based on the column of omop or have an LLM do this
                #  Actual random strings create hallucinations and confusion in the LLMs, so better change this
                #  ultimately

                fake = Faker()
                data[table][col] = [fake.sentence(nb_words=min(length // 10, 1)) for _ in range(config.SZ_SYNTHETIC_DB)]

            elif _type == "date":
                # TODO Create random dates that are not completely random to not confuse the LLM
                fake = Faker()
                data[table][col] = [fake.date() for _ in range(config.SZ_SYNTHETIC_DB)]
            elif _type == "datetime":
                # TODO Create random datetimes that are not completely random to not confuse the LLM
                fake = Faker()
                data[table][col] = [fake.date() for _ in range(config.SZ_SYNTHETIC_DB)]
            else:
                raise ValueError("Invalid synthetic database type")

        column_definitions = ', '.join(
            f"{col_name} {real_schema[col_name]}" for col_name, values in data[table].items()
        )
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({column_definitions});")

        columns = list(data[table].keys())
        rows = list(zip(*data[table].values()))

        placeholders = ", ".join("?" * len(columns))
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.executemany(query, rows)

    conn.commit()
    conn.close()
    return temp_db


def extract_schema(node):
    """
    Recursively extract a mapping of table/alias to set of columns used eliminating the views.
    :param node: glotsql node
    :return: mapping table to columns without temporary views
    """
    schema_mapping = {}

    alias_to_table = {}  # Map aliases to original table names

    # Collect all table aliases
    for table_ref in node.find_all(exp.Table):
        if table_ref.args.get("alias"):
            alias_to_table[table_ref.args["alias"].name] = table_ref.name

    # Process columns in the current node
    for col in node.find_all(exp.Column):
        table = col.table or "unknown"
        original_table = alias_to_table.get(table, table)

        column_name = col.name
        if isinstance(col.parent, exp.Alias):
            # The column is aliased, use the original name
            column_name = col.args.get("this").name if hasattr(col.args.get("this"), "name") else col.name

        schema_mapping.setdefault(original_table, set()).add(column_name)

    # Process any CTEs (temporary views) in the current node
    with_clause = node.args.get("with")
    if with_clause:
        for cte in with_clause.expressions:
            cte_name = cte.alias_or_name
            del schema_mapping[cte_name]

    return schema_mapping


def get_necessary_tables_and_columns(sql_alternatives: List[str]) -> Dict[str, List[str]]:
    """
    Extracts from a list of SQL code excerpt the tables and columns used in the queries
    :param sql_alternatives: list of SQL alternatives
    :return: dictionary from tables used to columns used within each table
    """
    table2column: Dict[str, Any] = {}

    valid_columns = []
    for table, cols in config.OMOP_SCHEMA.items():
        valid_columns += [col.split(" ")[0] for col in cols]


    for i, query in enumerate(sql_alternatives):
        # Parse the SQL query.

        qualified = None
        error_it = 0
        while qualified is None and error_it < config.MAX_NUMBER_COLUMN_ERRORS:
            try:
                parsed = parse_one(query)
                qualified = qualify(parsed, dialect="postgres", schema=config.OMOP_SCHEMA)
            except sqlglot.errors.OptimizeError as e:
                error_message = str(e)
                match = re.search(r'Column\s+[\'"]+"?(.+?)"?[\'"]\s+could not be resolved', error_message)
                if match:
                    unresolved_column = match.group(1)  # [1:-1]
                else:
                    break  # This should not happen ever

                # Get the best match if it meets the similarity threshold.
                matches = difflib.get_close_matches(unresolved_column, valid_columns, n=1, cutoff=0.6)
                closest_col = matches[0] if matches else unresolved_column
                query = query.replace(unresolved_column, closest_col)
                sql_alternatives[i] = query  # Given that we already tried to fix an error, lets save it to not lose it
                error_it += 1

        if qualified is None:  # This sql alternative will be lost due to column errors later
            continue

        # Get the mapping without the temporary views and add the uses to the mapping table2column
        mapping = extract_schema(qualified)
        for table, cols in mapping.items():
            if table in table2column:
                table2column[table].update(cols)
            else:
                table2column[table] = cols

    table2column = {table: list(cols) for table, cols in table2column.items()}
    return table2column


def database2str(uri: str) -> str:
    """
    Creates the string representation of the database
    :param uri: database uri
    :return:
    """
    # TODO Everything
    # Connect to your database
    conn = sqlite3.connect(uri)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()  # Returns a list of tuples

    db_str = ""
    for (table_name,) in tables:
        # Query all rows from your table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Retrieve column names from the cursor description
        headers = [description[0] for description in cursor.description]

        # Write the data to an in-memory string buffer as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)  # Write the header row
        writer.writerows(rows)  # Write all data rows

        csv_string = output.getvalue()
        db_str += f"Table {table_name}:\n" + csv_string + "\n\n"
        # Clean up
        output.close()
    conn.close()

    return db_str


