import os

# Change the current working directory to be consistent with docker's
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(script_dir, "..", ".."))

from flask import jsonify
from config import TEMPLATE_DIR, STATIC_DIR
from auth import token_required, keycloak_openid
from queries import *
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from queries import add_query, add_satisfaction
from celery import Celery, Task


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app() -> Flask:
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

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per hour", "10 per minute"],
    storage_uri="memory://",
)


@app.route(f'/')
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
def home():
    return render_template('index.html')


@app.route(f'{config.APP_NAME}/submit', methods=['POST'])
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
def login():
    """
    User login endpoint.

    This endpoint accepts a POST request with a JSON payload containing the user's
    username and password. If the credentials are valid, it returns a JSON response
    with a JWT token that the user can use for further communication with the system.

    :return: JSON Response, Status Code
    """
    try:
        username = request.form['username']
        password = request.form['password']
        try:
            token = keycloak_openid.token(username, password)
            return jsonify(token), 200
        except Exception as e:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": "Expected username and password credentials"}), 400


@app.route(f'{config.APP_NAME}/chat/', methods=['POST'])
@token_required
def request():
    """
    User chat endpoint.

    This endpoint accepts a POST request with a JSON payload containing the user's
    query and checks the required token in the header. If the credentials are valid,
    it returns a JSON response with query result.

    :return: JSON Response, Status Code
    """
    data = request.get_json()

    if 'text' in data:
        # Handle initial query
        user_message = data['text']

        # Convert the user message to a SQL query
        sql_query = text2SQL(user_message)

        # Execute the SQL query
        result = query(sql_query)

        # Format the result into a readable response
        response_message = f"Query result: {result}"

        # Generate a query_id to track the interaction
        query_id = add_query(user_message, sql_query)

        # Return the response and query_id
        return jsonify({'query_id': query_id, 'response': response_message}), 200

    elif 'query_id' in data and 'satisfactory' in data:
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
