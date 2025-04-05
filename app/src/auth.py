import base64

from keycloak import KeycloakOpenID
from flask import request, jsonify
from functools import wraps
import requests
from jose import jwt
import jose as jwk
import app.src.config as config
from jose import jwk


keycloak_openid = KeycloakOpenID(
    server_url=config.KEYCLOAK_SERVER,
    client_id=config.CLIENT_ID,
    realm_name=config.REALM_NAME,
    verify=True
)

def verify_token(token):
    # Introspect the token with client_id included
    token_info = keycloak_openid.introspect(
        token=token,
        # client_id=config.CLIENT_ID  # Explicitly pass client_id
    )

    if token_info["active"]:
        print("Token is valid.")
        return True
    else:
        print("Token is invalid.")
        return False


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
            return jsonify({"error": f"Invalid authorization header received. {auth_header}"}), 401
        try:
            access_token = auth_header
            _ = keycloak_openid.decode_token(
                token=access_token
            )
        except Exception as e:
            return jsonify({"error": f"Invalid token."}), 401
        return f(*args, **kwargs)
    return decorated

