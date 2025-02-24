import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path of the config.py file
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'your_database.db')
APP_NAME = "/PULSE"
KEYCLOAK_SERVER = "https://keycloak.example.com"
REALM_NAME = "myrealm"