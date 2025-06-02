import requests
from core.config import settings

"""
AuthService class for handling OAuth2 token retrieval using client credentials.

Attributes:
    client_id (str): The client ID for OAuth2 authentication.
    client_secret (str): The client secret for OAuth2 authentication.
    scope (str): The scope of the OAuth2 token.

Methods:
    get_access_token():
        Fetches an OAuth2 access token using client credentials.

Usage:
    # Instantiate the AuthService with your client credentials and scope
    auth_service = AuthService(client_id="your_client_id", client_secret="your_client_secret", scope="your_scope")
    
    # Retrieve the access token
    access_token = auth_service.get_access_token()
"""

# OAuth2 Endpoint
TOKEN_URL = settings.TOKEN_URL

class AuthService:
    """Handles OAuth2 token retrieval using client credentials."""

    def __init__(self, client_id: str, client_secret: str, scope: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope

    def get_access_token(self):
        """Fetch OAuth2 access token."""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
            "grant_type": "client_credentials"
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            f"{TOKEN_URL}?algorithm=RS256_2048&blind=false&compress=false&idjwt=false",
            data=payload, headers=headers
        )

        if response.status_code == 200:
            access_token = response.json().get("access_token")
            # print(f"Token Acquired: {access_token}")
            return access_token
        else:
            print(f"Failed to get token: {response.text}")
            return None

