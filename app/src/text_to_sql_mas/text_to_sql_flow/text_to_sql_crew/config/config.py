import os

OMOP_SYNTHETIC_DB_PARAMS = {
    "dbname": os.getenv("SYN_DB_NAME"),
    "user": os.getenv("SYN_DB_USER"),
    "password": os.getenv("SYN_DB_PASSWORD"),
    "host": os.getenv("SYN_DB_HOST"),
    "port": os.getenv("SYN_DB_PORT", "5432")  # Default to 5432 if not set
}