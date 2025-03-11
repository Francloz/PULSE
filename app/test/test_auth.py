import unittest
from auth import get_publickey, keycloak_openid


class TestKeycloakAuth(unittest.TestCase):
    def test_valid_token(self):
        # Given test credentials
        username = 'myuser'
        password = '1234'

        # Request a token from Keycloak
        try:
            token = keycloak_openid.token(username, password)
        except Exception as e:
            x = 0
        self.assertIsNotNone(token, "Token should not be None")

        # Prepare the public key for token decoding
        public_key = get_publickey()
        public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

        # Try decoding the token. If the token is invalid, this will raise an Exception.
        try:
            decoded_token = keycloak_openid.decode_token(
                token=token,
                key=public_key,
                options={"verify_signature": True, "verify_aud": True, "exp": True}
            )
        except Exception as e:
            self.fail(f"Decoding token failed: {e}")

        # Assert that the decoded token contains expected fields (e.g., expiration, audience)
        self.assertIsInstance(decoded_token, dict, "Decoded token should be a dictionary")
        self.assertIn("exp", decoded_token, "Token should contain an expiration field")
        self.assertIn("aud", decoded_token, "Token should contain an audience field")


if __name__ == '__main__':
    unittest.main()