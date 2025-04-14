BASIC_BACKGROUND = ("As a seasoned data engineer who has guided multiple clinical trials using the OMOP common "
                        "data model for statistical analysis")
DOUBT_DETECTION_PROMPT = (f"{BASIC_BACKGROUND}, "
                        "when a clinician requests data you know what information is incomplete for the queries "
                        "they asked for in a methodical and careful manner in order to preemptively solve "
                        "ambiguities that might arise when crafting queries for the database."
                        "\n---------\n"
                        "Is this query from a knowledgeable clinician sufficiently complete? Query: {"
                        "initial_inquiry}."
                        "Make any reasonable assumption understanding that the clinician has tried to be clear."
                        "\nIf it is very essential, give a list of questions the clinician should clarify. "
                        "Explain the necessity of each of them. Do it using JSON format:"
                        "[{{'question': question, 'reason': reason}},...]"
                        "\nEscape strings as necessary for correct formatting."
                        "\nIf no questions are very essential, give an empty list [].")

QUERY_REWRITE_PROMPT = (
    f"{BASIC_BACKGROUND}, when given a OMOP CDM database query in natural language, "
    "you can further refine it in a precise and methodical manner."
    "\n---------\n"
    "Given this query: '{initial_inquiry}' and this complementary information to decrease ambiguity {information}."
    "\nExplain in free text the query so that I can translate it to SQL. Do it in a way that is unambiguous and "
    "clear."
    "\nGive it using the following format: <<< Rewritten query: <query> >>>")

DECOMPOSITION_PROMPT = (
    f"{BASIC_BACKGROUND}, when given a OMOP CDM database query description, "
    "you know what steps would be required to translate the query to SQL. You think things in steps, "
    "methodically, and clearly to not make mistakes. You always pay attention to the details of the requests"
    "to not miss critical information. Your resulting query plans are efficient and concise."
    "\n---------\n"
    "Given this query: '{initial_inquiry}', explain without code all the sub-queries that create views that are "
    "required to perform the query including the temporary view it would create and what OMOP CDM tables and "
    "columns it would need."
    "\nUse the following format for each step: "
    "\n<number>: <description of the step in free text>"
    "\n<number>: <description of the step in free text>")

TRANSLATION_PROMPT = (
    f"{BASIC_BACKGROUND}, when given a OMOP CDM database query in natural language, "
    "you know how to translate it to SQL."
    "\n---------\n"
    "Given this query: '{query}', and these temporary views '{views}', translate the query to SQL."
    "\nUse the following format: "
    "\n---------"
    "\n```SQL "
    "\nCREATE VIEW <view_name> AS <SQL code>"
    "\n```")

TEST_DB_PROMPT = (
    f"{BASIC_BACKGROUND}, when given a OMOP CDM database SQL query and knowing the current state "
    f"of the database, you know what the result of the query would be."
    "\n---------\n"
    "Given:"
    "\n - Query: '{query}'"
    "\n - Database: '{database}'"
    "\nGive the result to me in csv format")

SIMULATE_SQL_ON_DB_PROMPT = (
    f"{BASIC_BACKGROUND}, when given a OMOP CDM database query in natural language and knowing the current state "
    f"of the database, you know what the result of the query would be. You always think things through step by "
    f"step, clearly and methodically."
    "\n---------\n"
    "Given:"
    "\n - Query: '{query}'"
    "\n - Database: '{database}'"
    "\nGive the final result to me in csv format using \nRESULT: <csv>")