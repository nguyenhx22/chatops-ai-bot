import streamlit as st
import urllib.parse
import requests
import structlog
from datetime import datetime, timedelta, timezone
from core.config import settings

log = structlog.get_logger()

class SSOAuth:
    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.redirect_uri = settings.REDIRECT_URI
        self.scope = "User.Read"
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.graph_api_url = "https://graph.microsoft.com/v1.0/me"

    def is_token_expired(self):
        if "token_expiry" not in st.session_state:
            log.info("Token expiry not found in session state, assuming expired.")
            return True
        expired = datetime.now(timezone.utc) >= st.session_state.token_expiry
        log.info("Token expiration check.", expired=expired)
        return expired

    def get_login_url(self):
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": self.scope,
        }
        login_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        log.info("Generated Microsoft login URL.", url=login_url)
        return login_url

    def get_access_token(self, auth_code=None, refresh_token=None):
        log.info("Fetching access token.", auth_code=bool(auth_code), refresh_token=bool(refresh_token))

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if auth_code:
            data.update({
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
            })
        elif refresh_token:
            data.update({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            })
        else:
            log.error("Neither authorization code nor refresh token provided.")
            st.error("Neither authorization code nor refresh token provided.")
            return None, None

        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            token_response = response.json()
            expires_in = token_response.get("expires_in", 3600)
            st.session_state.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            log.info("Access token retrieved successfully.", expires_in=expires_in)
            return token_response.get("access_token"), token_response.get("refresh_token")
        else:
            log.error("Failed to retrieve access token.", status_code=response.status_code, response=response.text)
            st.error("Failed to retrieve token")
            st.json(response.json())
            return None, None

    def get_user_profile(self, access_token):
        log.info("Fetching user profile from Microsoft Graph API.")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.graph_api_url, headers=headers)

        if response.status_code == 200:
            log.info("User profile retrieved successfully.")
            return response.json()
        else:
            log.error("Failed to retrieve user profile.", status_code=response.status_code, response=response.text)
            st.error("Failed to retrieve user profile")
            st.json(response.json())
            return None
