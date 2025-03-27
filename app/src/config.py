import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path of the config.py file
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
LOCAL_DATABASE_PATH = os.path.join(DATA_DIR, 'your_database.db')
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')

APP_NAME = "/PULSE"

KEYCLOAK_PARAMS = {
    "host": os.getenv("KEYCLOAK_HOST", "http://localhost"),
    "port": os.getenv("KEYCLOAK_PORT", "8080"),  # Default to 5432 if not set
    "client_id": os.getenv("KEYCLOAK_PULSE_CLIENT_ID", "myclient"),
    "client_secret": os.getenv("KEYCLOAK_PULSE_CLIENT_SECRET", ""),
    "realm": os.getenv("KEYCLOAK_PULSE_REALM", "myrealm"),
}

KEYCLOAK_SERVER = KEYCLOAK_PARAMS["host"] + ":" + KEYCLOAK_PARAMS["port"]
REALM_NAME = KEYCLOAK_PARAMS["realm"]
CLIENT_ID = KEYCLOAK_PARAMS["client_id"]
CLIENT_SECRET = KEYCLOAK_PARAMS["client_secret"]



OMOP_DOCS_PATH = "placeholder" # maybe this https://ohdsi.github.io/CommonDataModel/cdm54.html
OMOP_DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432")  # Default to 5432 if not set
}


# Ensure the directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Ensure the file exists
if not os.path.exists(LOCAL_DATABASE_PATH):
    with open(LOCAL_DATABASE_PATH, 'w'):
        pass  # Creates an empty file


NUM_SYNTHETIC_DB = 0
NUM_CONSISTENCY_REPLICATES = 1
ON_SQL_TEST_FAILURE = "SKIP"
CONTEXT_LIMIT = 1000