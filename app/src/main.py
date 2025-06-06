import os
import sys
import uuid

# Change the current working directory to be consistent with docker's
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(script_dir, "..", ".."))

from flask import jsonify, session, redirect, url_for, send_from_directory
from config import TEMPLATE_DIR, STATIC_DIR
from auth import login_required
from queries import *
from flask import Flask, render_template, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from queries import add_query, add_satisfaction
from celery import Celery, Task
import redis
from utils import ChatHandler, SessionHandler
from authlib.integrations.flask_client import OAuth


def celery_init_app(app: Flask) -> Celery:
    """
    Initialize the Celery application for the Flask instance.
    :param app: Flask instance.
    :return: celery instance.
    """
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def redis_init_client():
    """
    Initializes the redis client
    :return:
    """
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    return redis_client


def create_app() -> Flask:
    """
    Creates the Flask application with Redis support
    :return:
    """
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app


app = create_app()
redis_client = redis_init_client()
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per hour", "10 per minute"],
    storage_uri="memory://",
)

oauth = OAuth(app)
oauth.register(
    name="keycloak",
    client_id=config.KEYCLOAK_CLIENT_ID,
    client_secret=config.KEYCLOAK_CLIENT_SECRET,
    server_metadata_url=os.getenv("KEYCLOAK_SERVER_METADATA_URL"),
    client_kwargs={"scope": "openid profile email"},
)

@app.route(f'{config.APP_NAME}/index', methods=['POST'])
def index():
    return jsonify(
        {
            'name': 'PULSE REST API',
            'version': '0.0.0',
            'status': 'running',
            'authenticated': 'user' in session,  # Keycloak auth status
            'endpoints': {
                'login': '/login',
                'logout': '/logout',
                'protected': '/chat',
                'public': '/index'
            },
            'documentation': f'{config.APP_NAME}/docs',
        }
    )


@app.route(f'{config.APP_NAME}/docs', methods=['GET'])
def docs():
    return send_from_directory('templates', 'docs.html')

@app.route(f'{config.APP_NAME}/login', methods=['POST'])
def login():
    redirect_uri = url_for("auth", _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)

@app.route("/auth")
def auth():
    token = oauth.keycloak.authorize_access_token()
    session["user"] = oauth.keycloak.parse_id_token(token)
    return redirect("/")

@app.route('f{config.APP_NAME}/logout')
def logout():
    session.pop('user', None)
    session.pop('access_token', None)
    return redirect(url_for(f'{config.APP_NAME}/'))

@app.route(f'{config.APP_NAME}/chat', methods=['POST'])
@login_required
def chat_request():
    """
    User chat endpoint.

    This endpoint accepts a POST request with a JSON payload containing the user's
    query and checks the required token in the header. If the credentials are valid,
    it returns a JSON response with query result.

    :return: JSON Response, Status Code
    """
    data = request.get_json()

    if 'text' in data and 'username' in data:
        # Handle initial query
        user_message = data['text']
        if 'chat_id' in data:
            chat_id = data['chat_id']
        else:
            chat_id = str(uuid.uuid4())

        session_handler = SessionHandler(redis_client)
        session_handler.create_or_recover_session(g.user_id)
        chat_handler: ChatHandler = session_handler.chat_handler

        chat_handler.create_or_recover_chat(chat_id)
        chat_response = chat_handler.continue_chat(user_message)
        is_success = chat_handler.chat_state.outstanding_task is None

        if is_success:  # Execute the SQL query
            extract_query = lambda x: x  # placeholder
            sql_query = extract_query(chat_response)
            result = query(sql_query)

            # Format the result into a readable response
            response_message = f"Query result: {result}"

            # Generate a query_id to track the interaction
            query_id = add_query(user_message, sql_query,
                                 f"{session_handler.session_state.user_id}:{session_handler.session_state.session_id}:{chat_id}")

            # Return the response and query_id
            return jsonify({'chat_id': chat_id, 'chat_response': chat_response, 'query_result': result}), 200
        else:  # Send interruption text, such as a clarification request to the user
            return jsonify({'chat_id': chat_id, 'chat_response': chat_response}), 200

    elif 'query_id' in data and 'satisfactory' in data and 'username' in data:
        # Handle feedback
        query_id = data['query_id']
        is_satisfactory = data['is_satisfactory']

        # Check if the query_id exists
        if check_query_exists(query_id):
            add_satisfaction(query_id, is_satisfactory)
        else:
            return jsonify({'error': 'Query ID not found'}), 404

        # Respond with acknowledgment
        return jsonify({'message': 'Feedback received'}), 200
    else:
        return jsonify({'error': 'Invalid input'}), 400


if __name__ == '__main__':
    app.run(debug=True)
