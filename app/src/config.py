import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path of the config.py file
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'your_database.db')
APP_NAME = "/PULSE"
KEYCLOAK_SERVER = "http://localhost:8080"
REALM_NAME = "myrealm"
TEMPLATE_FOLDER = os.path.join(BASE_DIR, '..', 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, '..', 'static')
CLIENT_ID = "myclient"
OMOP_DOCS_PATH = "placeholder"

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
if not os.path.exists(DATABASE_PATH):
    with open(DATABASE_PATH, 'w'):
        pass  # Creates an empty file