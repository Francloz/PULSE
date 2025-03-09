from keycloak import KeycloakOpenID
from flask import request, jsonify
from functools import wraps
import requests
from jose import jwk
import app.src.config as config

keycloak_openid = KeycloakOpenID(
    server_url=config.KEYCLOAK_SERVER,
    client_id="example",
    client_secret_key="example_secret", # This sets up the connection to the client application
    realm_name=config.REALM_NAME,
    verify=True
)

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
            return jsonify({"error": "Invalid authorization header"}), 401

        try:
            public_key = get_publickey()
            public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
            token = auth_header.split(" ")[0]
            keycloak_openid.decode_token(
                token=token,
                key=public_key,
                options={"verify_signature":True, "verify_aud":True, "exp":True}
            )
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def get_publickey():
    """
    Get the public key of the keycloak realm.

    :return: public key
    """
    # URL to retrieve the JWKS
    jwks_url = f"{config.KEYCLOAK_SERVER}/realms/{config.REALM_NAME}/protocol/openid-connect/certs"

    # Fetch the JWKS
    response = requests.get(jwks_url)
    jwks = response.json()

    # The 'kid' value from the JWT header, which you need to match with one in the JWKS
    jwt_kid = "your_jwt_kid_here"

    # Find the correct key in the JWKS
    key = None
    for k in jwks['keys']:
        if k['kid'] == jwt_kid:
            key = k
            break

    if key:
        # Extract the RSA public key
        public_key = jwk.construct(key)
        print(public_key)
        return public_key
    else:
        raise FileNotFoundError("Public key not found")

