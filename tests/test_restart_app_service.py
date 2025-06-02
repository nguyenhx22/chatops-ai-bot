import requests
from core.config import settings
from auth.oauth_client import AuthService

# Configuration
CLIENT_ID = settings.CLIENT_ID_CHATOPS
CLIENT_SECRET = settings.CLIENT_SECRET_CHATOPS_SERVICE
SCOPE = settings.SCOPE_CHATOPS_SERVICE
API_URL = settings.API_URL_CHATOPS_SERVICE

# Instantiate AuthService
auth_service = AuthService(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scope=SCOPE
)


def restart_application(cf_app_name, cf_site, cf_org, cf_space):
    """Calls the /cloudfoundry/restart-application endpoint."""
    access_token = auth_service.get_access_token()
    if not access_token:
        print("Failed to retrieve access token.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "cf_app_name": cf_app_name,
        "cf_site": cf_site,
        "cf_org": cf_org,
        "cf_space": cf_space,
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        print("Application restart successful:", response.json())
        return response.json()
    else:
        print("Failed to restart application:", response.text)
        return None


# Example usage
if __name__ == "__main__":
    restart_application(
        cf_app_name="npp-chatops-e2e-service", cf_site="po-r2", cf_org="SE-APS-VOICE-PRD-PO", cf_space="NPP-R2"
    )
