# authentication_handler.py
import streamlit as st
import structlog
from auth.authentication import SSOAuth

class Authenticator:
    def __init__(self):
        self.log = structlog.get_logger()
        self.sso_auth = SSOAuth()

    def authenticate_user(self):
        auth_code = st.query_params.get("code")

        # CASE 1: Redirected from Azure login
        if auth_code:
            self.log.info("Authorization code received.")
            access_token, refresh_token = self.sso_auth.get_access_token(auth_code=auth_code)

            if access_token:
                st.session_state.access_token = access_token
                st.session_state.refresh_token = refresh_token
                st.query_params.clear()

                user_profile = self.sso_auth.get_user_profile(access_token)
                if user_profile:
                    display_name = user_profile.get("displayName")
                    try:
                        last_name, first_name = display_name.split(", ")
                        user_name = f"{first_name} {last_name}"
                    except ValueError:
                        user_name = display_name
                    user_id = user_profile.get("userPrincipalName", "").partition("@")[0].lower()
                    st.session_state.user_name = user_name
                    st.session_state.user_id = user_id
                    self.log.info("User profile loaded.", user=user_name)
                    return True, user_name, user_id

        # CASE 2: Valid access token
        elif "access_token" in st.session_state and not self.sso_auth.is_token_expired():
            self.log.info("Access token valid. Initializing chat.")
            return True, st.session_state.user_name, st.session_state.user_id

        # CASE 3: Token refresh path
        elif "refresh_token" in st.session_state:
            self.log.info("Attempting token refresh.")
            access_token, refresh_token = self.sso_auth.get_access_token(
                refresh_token=st.session_state.refresh_token
            )
            if access_token:
                st.session_state.access_token = access_token
                st.session_state.refresh_token = refresh_token
                return True, st.session_state.user_name, st.session_state.user_id

        # CASE 4: Not authenticated
        self.log.warning("User not authenticated. Showing login.")
        login_url = self.sso_auth.get_login_url()
        return False, login_url, None
