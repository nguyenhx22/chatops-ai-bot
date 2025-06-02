import json, requests, structlog
import streamlit as st
from core.config import settings
from backend.knowledge_base import (
    get_cloud_foundry_app_info,
    is_application_available_to_user,
)
from backend.chatops_service import (
    cf_restart_application_api,
    cf_start_application_api,
    cf_stop_application_api,
    cf_check_application_health_api,
)

# Added: Imports for Pydantic schemas
from pydantic import BaseModel, Field
from typing import (
    Type,
)  # Keep Type if needed elsewhere, though not strictly for these schemas

log = structlog.get_logger()


# --- Define Input Schemas for Tools ---
class GetAppInfoInput(BaseModel):
    """Input schema for get_application_information tool."""

    application: str = Field(description="The name of the Cloud Foundry application.")


class RestartAppInput(BaseModel):
    """Input schema for restart_application tool."""

    group_name: str = Field(
        description="The group name associated with the application."
    )
    application: str = Field(
        description="The name of the Cloud Foundry application to restart."
    )
    cloud_foundry_site: str = Field(
        description="The Cloud Foundry site identifier (e.g., 'po-r2')."
    )
    cf_organization: str = Field(
        description="The Cloud Foundry organization name where the app resides."
    )
    cf_space: str = Field(
        description="The Cloud Foundry space name where the app resides."
    )

class StartAppInput(BaseModel):
    """Input schema for start_application tool."""

    group_name: str = Field(
        description="The group name associated with the application."
    )
    application: str = Field(
        description="The name of the Cloud Foundry application to start."
    )
    cloud_foundry_site: str = Field(
        description="The Cloud Foundry site identifier (e.g., 'po-r2')."
    )
    cf_organization: str = Field(
        description="The Cloud Foundry organization name where the app resides."
    )
    cf_space: str = Field(
        description="The Cloud Foundry space name where the app resides."
    )

class StopAppInput(BaseModel):
    """Input schema for stop_application tool."""

    group_name: str = Field(
        description="The group name associated with the application."
    )
    application: str = Field(
        description="The name of the Cloud Foundry application to stop."
    )
    cloud_foundry_site: str = Field(
        description="The Cloud Foundry site identifier (e.g., 'po-r2')."
    )
    cf_organization: str = Field(
        description="The Cloud Foundry organization name where the app resides."
    )
    cf_space: str = Field(
        description="The Cloud Foundry space name where the app resides."
    )

class CheckHealthAppInput(BaseModel):
    """Input schema for check_application_health tool."""

    group_name: str = Field(
        description="The group name associated with the application."
    )
    application: str = Field(
        description="The name of the Cloud Foundry application to check health."
    )
    cloud_foundry_site: str = Field(
        description="The Cloud Foundry site identifier (e.g., 'po-r2')."
    )
    cf_organization: str = Field(
        description="The Cloud Foundry organization name where the app resides."
    )
    cf_space: str = Field(
        description="The Cloud Foundry space name where the app resides."
    )

class CloudFoundryTools:

    @staticmethod
    def get_application_information(application: str) -> str:
        """
        Retrieves application information based on the application name.

        Args:
            application: The name of the Cloud Foundry application.

        Returns:
            A string containing the retrieved context or an error message.
        """
        log.info("Retrieving application information.", application=application)
        try:
            # Directly use the application argument
            if not application:
                log.warning("Application name is missing.")
                return "Error: Missing 'application' argument."

            # Call the backend function
            result = get_cloud_foundry_app_info(application)
            log.info(
                "Successfully retrieved application context.",
                application=application,
                result_length=len(str(result)),
            )
            # Return the result
            return f"Context Retrieved: {result}"

        except Exception as e:
            log.error(
                "Error retrieving application info",
                application=application,
                error=str(e),
                exc_info=True,
            )
            return f"Error: An unexpected error occurred while processing your request for application '{application}'."

    @staticmethod
    def restart_application(
        application: str,
        group_name: str,
        cloud_foundry_site: str,
        cf_organization: str,
        cf_space: str,
    ) -> str:
        """
        Restarts a Cloud Foundry application after checking permissions.

        Args:
            application: The name of the application to restart.
            group_name: The group name for permission checking.
            cloud_foundry_site: The CF site identifier.
            cf_organization: The CF organization name.
            cf_space: The CF space name.

        Returns:
            A string indicating success, permission denial, or an error message.
        """
        log.info(
            "Attempting to restart Cloud Foundry application.",
            application=application,
            group_name=group_name,
            site=cloud_foundry_site,
            org=cf_organization,
            space=cf_space,
        )
        try:
            # Check if the application name is provided
            if not is_application_available_to_user(
                user_id=st.session_state.user_id,
                group_name=group_name,
                cf_app_name=application,
            ):
                log.warning(
                    "Permission denied for application restart.",
                    application=application,
                    group_name=group_name,
                )
                return f"Your do not have permission to restart {application}. Please ensure the application name is correct and you have the necessary permissions."
            log.info(
                "Permission check passed.",
                application=application,
                group_name=group_name,
            )

            # Call the backend restart function with direct arguments
            response = cf_restart_application_api(
                application,
                cloud_foundry_site,
                cf_organization,
                cf_space,
            )
            log.info(
                "Application restart command executed successfully.",
                application=application,
            )

            return response

        except Exception as e:
            log.error(
                "Error restarting application",
                application=application,
                group_name=group_name,
                site=cloud_foundry_site,
                org=cf_organization,
                space=cf_space,
                error=str(e),
                exc_info=True,
            )
            return f"Error: An unexpected error occurred while attempting to restart application '{application}'. Exception: {str(e)}"

    @staticmethod
    def start_application(
        application: str,
        group_name: str,
        cloud_foundry_site: str,
        cf_organization: str,
        cf_space: str,
    ) -> str:
        """
        Starts a Cloud Foundry application after checking permissions.

        Args:
            application: The name of the application to start.
            group_name: The group name for permission checking.
            cloud_foundry_site: The CF site identifier.
            cf_organization: The CF organization name.
            cf_space: The CF space name.

        Returns:
            A string indicating success, permission denial, or an error message.
        """
        log.info(
            "Attempting to start Cloud Foundry application.",
            application=application,
            group_name=group_name,
            site=cloud_foundry_site,
            org=cf_organization,
            space=cf_space,
        )
        try:
            # Check if the application name is provided
            if not is_application_available_to_user(
                user_id=st.session_state.user_id,
                group_name=group_name,
                cf_app_name=application,
            ):
                log.warning(
                    "Permission denied for starting an application.",
                    application=application,
                    group_name=group_name,
                )
                return f"Your do not have permission to start {application}. Please ensure the application name is correct and you have the necessary permissions."
            log.info(
                "Permission check passed.",
                application=application,
                group_name=group_name,
            )

            # Call the backend start function with direct arguments
            response = cf_start_application_api(
                application,
                cloud_foundry_site,
                cf_organization,
                cf_space,
            )
            log.info(
                "Application start command executed successfully.",
                application=application,
            )

            return response

        except Exception as e:
            log.error(
                "Error starting application",
                application=application,
                group_name=group_name,
                site=cloud_foundry_site,
                org=cf_organization,
                space=cf_space,
                error=str(e),
                exc_info=True,
            )
            return f"Error: An unexpected error occurred while attempting to starting application '{application}'. Exception: {str(e)}"

    @staticmethod
    def stop_application(
        application: str,
        group_name: str,
        cloud_foundry_site: str,
        cf_organization: str,
        cf_space: str,
    ) -> str:
        """
        Stops a Cloud Foundry application after checking permissions.

        Args:
            application: The name of the application to stop.
            group_name: The group name for permission checking.
            cloud_foundry_site: The CF site identifier.
            cf_organization: The CF organization name.
            cf_space: The CF space name.

        Returns:
            A string indicating success, permission denial, or an error message.
        """
        log.info(
            "Attempting to stop Cloud Foundry application.",
            application=application,
            group_name=group_name,
            site=cloud_foundry_site,
            org=cf_organization,
            space=cf_space,
        )
        try:
            # Check if the application name is provided
            if not is_application_available_to_user(
                user_id=st.session_state.user_id,
                group_name=group_name,
                cf_app_name=application,
            ):
                log.warning(
                    "Permission denied for stopping an application.",
                    application=application,
                    group_name=group_name,
                )
                return f"Your do not have permission to stop {application}. Please ensure the application name is correct and you have the necessary permissions."
            log.info(
                "Permission check passed.",
                application=application,
                group_name=group_name,
            )

            # Call the backend stop function with direct arguments
            response = cf_stop_application_api(
                application,
                cloud_foundry_site,
                cf_organization,
                cf_space,
            )
            log.info(
                "Application stop command executed successfully.",
                application=application,
            )

            return response

        except Exception as e:
            log.error(
                "Error stopping application",
                application=application,
                group_name=group_name,
                site=cloud_foundry_site,
                org=cf_organization,
                space=cf_space,
                error=str(e),
                exc_info=True,
            )
            return f"Error: An unexpected error occurred while attempting to stop application '{application}'. Exception: {str(e)}"
        
    
    @staticmethod
    def check_application_health(
        application: str,
        group_name: str,
        cloud_foundry_site: str,
        cf_organization: str,
        cf_space: str,
    ) -> str:
        """
        Checks health of a Cloud Foundry application after checking permissions.

        Args:
            application: The name of the application to check health.
            group_name: The group name for permission checking.
            cloud_foundry_site: The CF site identifier.
            cf_organization: The CF organization name.
            cf_space: The CF space name.

        Returns:
            A string indicating success, permission denial, or an error message.
        """
        log.info(
            "Attempting to check health Cloud Foundry application.",
            application=application,
            group_name=group_name,
            site=cloud_foundry_site,
            org=cf_organization,
            space=cf_space,
        )
        try:
            # Call the backend health check function with direct arguments
            response = cf_check_application_health_api(
                application,
                cloud_foundry_site,
                cf_organization,
                cf_space,
            )
            log.info(
                "Application check health command executed successfully.",
                application=application,
            )

            return response

        except Exception as e:
            log.error(
                "Error checking health application",
                application=application,
                group_name=group_name,
                site=cloud_foundry_site,
                org=cf_organization,
                space=cf_space,
                error=str(e),
                exc_info=True,
            )
            return f"Error: An unexpected error occurred while attempting to check health application '{application}'. Exception: {str(e)}"