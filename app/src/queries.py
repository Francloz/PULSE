import config
import sqlite3

from multiagent.flow import Text2SQLFlow


def text2sql(text, username):
    """
    Given text that represents a natural language query (NLQ), returns the translated SQL code.

    :param username:
    :param text: natural language query
    :return: SQL code
    """
    flow_instance = Text2SQLFlow(username=username, initial_inquiry=text)
    result = flow_instance.kickoff()
    return result

def query(sql_query):
    """
    Given a SQL query, gets the result from the OMOP DB

    :param sql_query: SQL code
    :return: TODO
    """
    return None

def get_query_db_connection():
    """
    Returns the connection to the query database.

    :return: sqlite3 connection
    """
    conn = sqlite3.connect(config.LOCAL_DATABASE_PATH, check_same_thread=False)
    return conn

def create_query_table():
    """
    Checks that query tables are created.

    :return: None
    """
    conn = get_query_db_connection()
    cur = conn.cursor()

    # 'query_id', 'text', 'sql_query', 'satisfaction'
    cur.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                sql_query TEXT NOT NULL,
                is_satisfied BOOL
            )
        """)

    conn.commit()
    conn.close()

def add_satisfaction(id, is_satisfied):
    """
    Add the satisfaction to a query to the database of queries.

    :param id: query id
    :param is_satisfied: boolean signifying satisfaction
    :return:
    """
    conn = get_query_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE queries SET is_satisfied = ? WHERE id = ?", (is_satisfied, id))
    conn.commit()
    conn.close()

def check_query_exists(id) -> bool:
    """
    Checks that the query id exists in the database.

    :param id: query id
    :return: boolean
    """
    conn = get_query_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT EXISTS(SELECT 1 FROM queries WHERE id = ?)", (id,))
    exists = cur.fetchone()[0]

    conn.commit()
    conn.close()
    return bool(exists)

def add_query(text, sql_query):
    """
    Adds the query to the database of queries.

    :param text: natural language query
    :param sql_query: sql query
    :return: None
    """
    conn = get_query_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO queries(text, sql_query) VALUES (?, ?)", (text, sql_query))

    new_row_id = cur.lastrowid

    conn.commit()
    conn.close()
    return new_row_id

create_query_table()