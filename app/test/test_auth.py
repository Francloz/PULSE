import time
import unittest
from auth import keycloak_openid, verify_token
from cryptography.hazmat.primitives import serialization
import requests
import jwt


class TestKeycloakAuth(unittest.TestCase):
    def test_valid_token(self):
        # Given test credentials
        username = 'myuser'
        password = '1234'

        # Request a token from Keycloak
        try:
            token = keycloak_openid.token(username, password)
        except Exception as e:
            self.fail(f"Getting the token given username and password failed: {e}")
        self.assertIsNotNone(token, "Token should not be None")

        # Try decoding the token. If the token is invalid, this will raise an Exception.
        try:
            decoded_token = keycloak_openid.decode_token(
                token=token["access_token"]
            )
        except Exception as e:
            self.fail(f"Decoding token failed: {e}")

        # Assert that the decoded token contains expected fields (e.g., expiration, audience)
        self.assertIsInstance(decoded_token, dict, "Decoded token should be a dictionary")
        self.assertIn("exp", decoded_token, "Token should contain an expiration field")
        self.assertIn("aud", decoded_token, "Token should contain an audience field")

    def test_invalid_credentials(self):
        with self.assertRaises(Exception):
            keycloak_openid.token('wronguser', 'wrongpass')

    def test_expired_token(self):
        # Get a valid token first
        token = keycloak_openid.token('myuser', '1234')

        verify_token(token["access_token"])

        # Simulate expiration (or use a pre-expired test token)
        time.sleep(10)  # Adjust based on your token lifespan

        with self.assertRaises(Exception):
            keycloak_openid.decode_token(token['access_token'], validate=True)
            x = 1

    def test_tampered_token(self):
        valid_token = keycloak_openid.token('myuser', '1234')['access_token']
        tampered_token = valid_token[:-4] + "abcd"  # Simple tampering example

        with self.assertRaises(Exception):
            keycloak_openid.decode_token(tampered_token)

    def test_wrong_audience(self):
        token = keycloak_openid.token('myuser', '1234')['access_token']
        decoded = keycloak_openid.decode_token(token)
        self.assertNotEqual(decoded['aud'], 'wrong-audience', "Token audience validation failed")

    def test_missing_claims(self):
        token = keycloak_openid.token('myuser', '1234')['access_token']
        decoded = keycloak_openid.decode_token(token)
        required_claims = ['sub', 'iss', 'exp']
        for claim in required_claims:
            self.assertIn(claim, decoded, f"Missing required claim: {claim}")

    def test_token_refresh(self):
        # Get initial token
        token = keycloak_openid.token('myuser', '1234')
        refresh_token = token['refresh_token']

        # Test valid refresh
        new_token = keycloak_openid.refresh_token(refresh_token)
        self.assertIsNotNone(new_token['access_token'])

        # Test invalid refresh
        with self.assertRaises(Exception):
            keycloak_openid.refresh_token('invalid_refresh_token')

    def test_malformed_token(self):
        malformed_tokens = [
            'invalid.token.format',
            'Bearer',
            '',
            None
        ]

        for token in malformed_tokens:
            with self.subTest(token=token):
                with self.assertRaises(Exception):
                    keycloak_openid.decode_token(token)

if __name__ == '__main__':
    unittest.main()