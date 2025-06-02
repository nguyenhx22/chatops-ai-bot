import structlog
import requests
import threading
from core.config import settings
from auth.oauth_client import AuthService

# Initialize logger
log = structlog.get_logger()

# Instantiate AuthService
auth_service = AuthService(
    client_id=settings.CLIENT_ID_CHATOPS,
    client_secret=settings.CLIENT_SECRET_CHATOPS_SERVICE,
    scope=settings.SCOPE_CHATOPS_SERVICE,
)

def _make_chatops_request(method, endpoint_url, payload=None, run_async=False):
    """Helper function to make authenticated requests to the chatops-service.

    If run_async is True, the request is made in a separate thread.
    """
    def _send_request():
        log.info(
            "Preparing to call chatops-service endpoint.",
            method=method,
            url=endpoint_url,
            payload=payload,
        )
        access_token = auth_service.get_access_token()
        if not access_token:
            log.error("Failed to retrieve access token for chatops-service.")
            return {"status": "error", "message": "Failed to retrieve access token."}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method, endpoint_url, json=payload, headers=headers, timeout=300
            )
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
            log.info(
                "Chatops-service endpoint call successful.",
                url=endpoint_url,
                status_code=response.status_code,
            )
            # Return the actual JSON response from the service on success
            return response.json()
        except requests.exceptions.HTTPError as e:
            log.error(
                "HTTP error calling chatops-service endpoint.",
                url=endpoint_url,
                status_code=e.response.status_code if e.response else "N/A",
                response_text=e.response.text if e.response else "N/A",
                error=str(e),
            )
            return {
                "status": "error",
                "message": f"API request failed with status {e.response.status_code if e.response else 'N/A'}: {e.response.text if e.response else 'No response text'}",
                "details": str(e),
                "status_code": e.response.status_code if e.response else None
            }
        except requests.RequestException as e:
            log.error(
                "Exception during chatops-service endpoint call.",
                url=endpoint_url,
                error=str(e),
            )
            return {
                "status": "error",
                "message": "Request to service failed.",
                "details": str(e),
            }
        except ValueError as e: # Handles cases where response.json() fails
            log.error(
                "Failed to decode JSON response from chatops-service.",
                url=endpoint_url,
                error=str(e),
            )
            return {
                "status": "error",
                "message": "Failed to decode JSON response from service.",
                "details": str(e),
            }


    if run_async:
        # run_async is True, run the request in a separate thread
        thread = threading.Thread(target=_send_request)
        thread.start()
        # For async, we can only confirm initiation.
        return {"status": "pending", "message": "Request has been initiated in background thread."}
    else:
        return _send_request()

def cf_restart_application_api(cf_app_name, cf_site, cf_org, cf_space):
    """Calls the chatops-service restart-application endpoint SYNCHRONOUSLY
    and returns the direct response from the service.
    """
    log.info(
        "Initiating application restart request (synchronous).",
        application=cf_app_name,
        site=cf_site,
    )

    payload = {
        "cf_app_name": cf_app_name,
        "cf_site": cf_site,
        "cf_org": cf_org,
        "cf_space": cf_space,
    }

    # Call the unified request function synchronously
    response = _make_chatops_request(
        method="POST",
        endpoint_url=settings.API_URL_CHATOPS_CF_RESTART,
        payload=payload,
        run_async=False
    )

    # If _make_chatops_request returned our structured error, pass it through.
    # Otherwise, 'response' is the direct JSON from the service.
    if isinstance(response, dict) and response.get("status") == "error":
        return response

    # If not an error, 'response' is the direct JSON from the service.
    # The service's response might indicate success, failure, or next steps.
    log.info(
        "Application restart request processed.",
        application=cf_app_name,
        site=cf_site,
        service_response=response # Log the actual service response
    )
    return response


def cf_start_application_api(cf_app_name, cf_site, cf_org, cf_space):
    """Calls the chatops-service start-application endpoint SYNCHRONOUSLY
    and returns the direct response from the service.
    """
    log.info(
        "Initiating application start request (synchronous).",
        application=cf_app_name,
        site=cf_site,
    )

    payload = {
        "cf_app_name": cf_app_name,
        "cf_site": cf_site,
        "cf_org": cf_org,
        "cf_space": cf_space,
    }

    # Call the unified request function synchronously
    response = _make_chatops_request(
        method="POST",
        endpoint_url=settings.API_URL_CHATOPS_CF_START,
        payload=payload,
        run_async=False
    )

    # If _make_chatops_request returned our structured error, pass it through.
    # Otherwise, 'response' is the direct JSON from the service.
    if isinstance(response, dict) and response.get("status") == "error":
        return response

    # If not an error, 'response' is the direct JSON from the service.
    log.info(
        "Application start request processed.",
        application=cf_app_name,
        site=cf_site,
        service_response=response # Log the actual service response
    )
    return response


def cf_stop_application_api(cf_app_name, cf_site, cf_org, cf_space):
    """Calls the chatops-service stop-application endpoint SYNCHRONOUSLY
    and returns the direct response from the service.
    """
    log.info(
        "Initiating application stop request (synchronous).",
        application=cf_app_name,
        site=cf_site,
    )

    payload = {
        "cf_app_name": cf_app_name,
        "cf_site": cf_site,
        "cf_org": cf_org,
        "cf_space": cf_space,
    }

    # Call the unified request function synchronously
    response = _make_chatops_request(
        method="POST",
        endpoint_url=settings.API_URL_CHATOPS_CF_STOP,
        payload=payload,
        run_async=False
    )

    # If _make_chatops_request returned our structured error, pass it through.
    # Otherwise, 'response' is the direct JSON from the service.
    if isinstance(response, dict) and response.get("status") == "error":
        return response

    # If not an error, 'response' is the direct JSON from the service.
    log.info(
        "Application stop request processed.",
        application=cf_app_name,
        site=cf_site,
        service_response=response # Log the actual service response
    )
    return response

def cf_check_application_health_api(cf_app_name, cf_site, cf_org, cf_space):
    """Calls the chatops-service check-application-health endpoint SYNCHRONOUSLY
    and returns the direct response from the service.
    """
    log.info(
        "Initiating application health request (synchronous).",
        application=cf_app_name,
        site=cf_site,
    )

    payload = {
        "cf_app_name": cf_app_name,
        "cf_site": cf_site,
        "cf_org": cf_org,
        "cf_space": cf_space,
    }

    # Call the unified request function synchronously
    response = _make_chatops_request(
        method="POST",
        endpoint_url=settings.API_URL_CHATOPS_CF_CHECK_HEALTH,
        payload=payload,
        run_async=False
    )

    # If _make_chatops_request returned our structured error, pass it through.
    # Otherwise, 'response' is the direct JSON from the service.
    if isinstance(response, dict) and response.get("status") == "error":
        return response

    # If not an error, 'response' is the direct JSON from the service.
    log.info(
        "Application health request processed.",
        application=cf_app_name,
        site=cf_site,
        service_response=response # Log the actual service response
    )
    return response