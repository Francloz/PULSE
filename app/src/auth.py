import base64
import uuid
from typing import Optional
from warnings import deprecated
from keycloak import KeycloakOpenID
from flask import request, jsonify, g
from functools import wraps
import requests
from jose import jwt
import jose as jwk
import app.src.config as config
from jose import jwk
from main import redis_client

keycloak_openid = KeycloakOpenID(
    server_url=config.KEYCLOAK_SERVER,
    client_id=config.CLIENT_ID,
    realm_name=config.REALM_NAME,
    verify=True
)


def get_or_create_user(username: Optional[str] = None, access_token: Optional[str] = None, ex=3600):
    """
    Gets or creates an user id from an username and or access token
    :param username:
    :param access_token:
    :param ex:
    :return:
    """
    assert username is not None or access_token is not None, "Either username or access token is required"
    if username is None:
        user_id = redis_client.get(f"token:{access_token}")
        if user_id:
            user_id = user_id.decode()
        else:
            raise ValueError("When giving only an access token, the user id must already exist")
    else:
        user_id = redis_client.get(f"user:{username}")
        if user_id:
            user_id = user_id.decode()
        else:
            user_id = str(uuid.uuid4())
            redis_client.set(f"user:{username}", user_id, ex=ex)
            if access_token:
                redis_client.set(f"token:{access_token}", user_id, ex=ex)
            redis_client.set(f"user_id:{user_id}", username, ex=ex)
    return user_id

def get_username(user_id: str):
    """
    Get username from the session map of user id to usernames.
    :param user_id: user id
    :return: username
    """
    username = redis_client.get(f"user_id:{user_id}")
    if username:
        username = username.decode()
    else:
        raise ValueError("The user id is not associated with any username")
    return username

def any_credentials_required(f):
    """
    Wrapper that checks the REST API incoming message header to find credentials.
    It accepts either 'basic', which should be a Base64 encoded string as follows
        username:credentials
    Or 'bearer', which should be a valid access token.

    If the credentials for 'basic' are given, the returning message will include an access token so that
    successive requests can be made using that access token instead of sending username and password.

    Example:
        Authorization bearer dXNlcm5hbWU6cGFzc3dvcmQ....

    :param f: function that receives a REST API message
    :return: wrapped function with authorization
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": f"No Authorization found in the header. Received:{auth_header}"}), 401
        scheme, encoded_credentials = auth_header.split(" ")

        if len(auth_header.split()) != 2:
            return jsonify({
                "error": f"Invalid authorization header. Expected two elements separated with a space. {auth_header}"}), 401

        if scheme.lower() == "basic":
            try:
                decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                username, password = decoded_credentials.split(':', 1)
                token = keycloak_openid.token(username, password)
                g.user_id = get_or_create_user(username, access_token=token)
            except Exception as e:
                return jsonify({"error": f"Failed to decode the token. This could be caused by an invalid token."}), 401

            response = f(*args, **kwargs)

            if isinstance(response, dict):
                response.update({"token": token})
                wrapped_response = response
            elif hasattr(response, "get_json") and callable(response.get_json):
                # If response is a Flask Response object with JSON
                data = response.get_json() or {}
                data.update({"token": token})
                wrapped_response = jsonify(data)
            else:
                # For any other response type
                wrapped_response = jsonify({"token": token, "original_response": response})
        elif scheme.lower() == "bearer":
            try:
                access_token = encoded_credentials
                _ = keycloak_openid.decode_token(token=access_token)
            except Exception as e:
                return jsonify({"error": f"Failed to decode the token. This could be caused by an invalid token."}), 401
            wrapped_response = f(*args, **kwargs)
        else:
            return jsonify(
                {"error": f"Expected the authorization header to be \"bearer <access token>\". {auth_header}"}), 401
        return wrapped_response

    return decorated


@deprecated
def user_credentials_required(f):
    """
    Creates a wrap that checks the REST header in order to check the credentials and adds the token that was given by
    Keycloak for those credentials after validating it.

    :param f:
    :return:
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": f"No Authorization found in the header. Received:{auth_header}"}), 401
        scheme, encoded_credentials = auth_header.split(" ")

        if len(auth_header.split()) != 2:
            return jsonify({
                               "error": f"Invalid authorization header. Expected two elements separated with a space. {auth_header}"}), 401
        if scheme.lower() != "basic":
            return jsonify(
                {"error": f"Expected the authorization header to be \"bearer <access token>\". {auth_header}"}), 401
        try:
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            token = keycloak_openid.token(username, password)
        except Exception as e:
            return jsonify({"error": f"Failed to decode the token. This could be caused by an invalid token."}), 401

        response = f(*args, **kwargs)

        if isinstance(response, dict):
            response.update({"token": token})
            wrapped_response = response
        elif hasattr(response, "get_json") and callable(response.get_json):
            # If response is a Flask Response object with JSON
            data = response.get_json() or {}
            data.update({"token": token})
            wrapped_response = jsonify(data)
        else:
            # For any other response type
            wrapped_response = jsonify({"token": token, "original_response": response})
        return wrapped_response

    return decorated


@deprecated
def token_required(f):
    """
    Creates a wrap that checks the REST header in order to check the token that was given during login.

    :param f:
    :return:
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": f"No Authorization found in the header. Received:{auth_header}"}), 401
        scheme, credential = auth_header.split(" ")
        if len(auth_header.split()) != 2:
            return jsonify({
                               "error": f"Invalid authorization header. Expected two elements separated with a space. {auth_header}"}), 401
        if scheme.lower() != "bearer":
            return jsonify(
                {"error": f"Expected the authorization header to be \"bearer <access token>\". {auth_header}"}), 401
        try:
            access_token = auth_header
            _ = keycloak_openid.decode_token(
                token=access_token
            )
        except Exception as e:
            return jsonify({"error": f"Failed to decode the token. This could be caused by an invalid token."}), 401
        return f(*args, **kwargs)

    return decorated
