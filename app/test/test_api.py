import time
import unittest
from auth import keycloak_openid, verify_token
from cryptography.hazmat.primitives import serialization
import requests
import jwt


class TestAPI(unittest.TestCase):
    def test_api(self):
        login_url = "http://127.0.0.1:5000/PULSE/submit"
        request_url = "http://127.0.0.1:5000/PULSE/chat"


        # Basic Auth
        response = requests.post(login_url, json={"username": "myuser", "password": "1234"})
        response_json = response.json()
        token = response_json["access_token"]

        # Bearer Token
        payload = {"text": "Give me the average age of all patients", "username": "myuser"}
        bad_headers = {"Authorization": f"b{token}"}
        bad_token_response = requests.post(request_url, headers=bad_headers, json=payload)

        bad_payload = {"hello": "Give me the average age of all patients", "username": "myuser"}
        headers = {"Authorization": f"{token}"}
        bad_payload_response = requests.post(request_url, headers=headers, json=bad_payload)

        payload = {"text": "Give me the average age of all patients", "username": "myuser"}
        headers = {"Authorization": f"{token}"}
        good_payload_response = requests.post(request_url, headers=headers, json=payload)


        pass