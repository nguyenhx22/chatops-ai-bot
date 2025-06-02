import streamlit as st
import json
import structlog
from backend.db_service import PostgresDB

# Initialize logger
log = structlog.get_logger()

# Instantiate DB service
db = PostgresDB()


def get_cloud_foundry_info() -> str:
    log.info("Fetching Cloud Foundry information.")
    user_id = st.session_state.user_id

    try:
        tasks = db.execute_query(
            """
            SELECT task_name AS cloud_foundry_task
            FROM public.chatops_tasks
            WHERE enabled = 'Y' AND task_type = 'CLOUD FOUNDRY'
        """,
            dict_cursor=True,
        )
        results1 = (
            json.dumps(
                [{"CLOUD_FOUNDRY_TASKS": [row["cloud_foundry_task"] for row in tasks]}],
                indent=2,
            )
            if tasks
            else "[]"
        )

        rows = db.execute_query(
            """
            SELECT DISTINCT a.group_name, b.cf_site AS cloud_foundry_site
            FROM public.chatops_users a
            JOIN public.chatops_org_space b ON a.group_name = b.group_name
            WHERE a.userid = %s
            ORDER BY 1, 2
        """,
            (user_id,),
            dict_cursor=True,
        )

        grouped_data = {}
        for item in rows:
            group_name = item["group_name"]
            site = item["cloud_foundry_site"]
            grouped_data.setdefault(
                group_name, {"GROUP_NAME": group_name, "CLOUD_FOUNDRY_SITES": []}
            )
            if site not in grouped_data[group_name]["CLOUD_FOUNDRY_SITES"]:
                grouped_data[group_name]["CLOUD_FOUNDRY_SITES"].append(site)
        results2 = json.dumps(list(grouped_data.values()), indent=2) if rows else "[]"

        rows = db.execute_query(
            """
            SELECT DISTINCT a.group_name, b.application
            FROM public.chatops_users a
            JOIN public.chatops_app_groups b ON a.group_name = b.group_name
            WHERE a.userid = %s
            ORDER BY 1, 2
        """,
            (user_id,),
            dict_cursor=True,
        )

        grouped_data = {}
        for item in rows:
            group_name = item["group_name"]
            app = item["application"]
            grouped_data.setdefault(
                group_name, {"GROUP_NAME": group_name, "APPLICATIONS": []}
            )
            if app not in grouped_data[group_name]["APPLICATIONS"]:
                grouped_data[group_name]["APPLICATIONS"].append(app)
        results3 = json.dumps(list(grouped_data.values()), indent=2) if rows else "[]"

        return f"{results1}\n\n{results2}\n\n{results3}"

    except Exception as e:
        return f"Unexpected Error: {str(e)}"


def get_ira_information(input_text: str) -> str:
    log.info("get_ira_information")
    ira_info = {
        "application": "IRA - Incident Resolution Assistant",
        "components": [{"Platform_Name": "mpa"}],
    }
    return json.dumps(ira_info, indent=2)


def get_ira_agent_context() -> str:
    log.info("get_ira_agent_context")
    ira_information = get_ira_information("")
    return f"Incident Resolution Assistant (IRA):\n{ira_information}"


def get_cf_agent_context() -> str:
    log.info("get_cf_agent_context")
    cloud_foundry_info = get_cloud_foundry_info()
    return f"Cloud Foundry Task Application:\n{cloud_foundry_info}"


def get_cloud_foundry_app_info(application: str) -> str:
    log.info("get_cloud_foundry_app_info")
    user_id = st.session_state.user_id

    try:
        rows = db.execute_query(
            """
            SELECT a.application, a.group_name, b.cf_site, b.cf_organization, b.cf_space
            FROM public.chatops_app_groups a
            JOIN public.chatops_org_space b ON a.group_name = b.group_name
            JOIN public.chatops_users c ON a.group_name = c.group_name
            WHERE LOWER(c.userid) = LOWER(%s) 
              AND LOWER(%s) LIKE '%%' || LOWER(a.application) || '%%'
        """,
            (user_id, application),
            dict_cursor=True,
        )

        grouped_data = {}
        for item in rows:
            key = (item["application"], item["group_name"])
            grouped_data.setdefault(
                key,
                {
                    "APPLICATION": item["application"],
                    "GROUP_NAME": item["group_name"],
                    "DETAILS": [],
                },
            )
            grouped_data[key]["DETAILS"].append(
                {
                    "CF_SITE": item["cf_site"],
                    "CF_ORGANIZATION": item["cf_organization"],
                    "CF_SPACE": item["cf_space"],
                }
            )

        return json.dumps(list(grouped_data.values()), indent=2) if rows else "[]"

    except Exception as e:
        return f"Unexpected Error: {str(e)}"


def get_application_groups() -> str:
    log.info("get_application_groups")
    user_id = st.session_state.user_id

    try:
        rows = db.execute_query(
            """
            SELECT group_name
            FROM public.chatops_users
            WHERE userid = %s
        """,
            (user_id,),
            fetch=True,
            dict_cursor=True,
        )

        groups = [row["group_name"] for row in rows]
        return (
            "\n".join([f"<li>{group}</li>" for group in groups])
            if rows
            else "No application groups found."
        )

    except Exception as e:
        return f"Unexpected Error: {str(e)}"


def get_cloud_foundry_tasks() -> str:
    log.info("get_cloud_foundry_tasks")

    try:
        rows = db.execute_query(
            """
            SELECT task_name
            FROM public.chatops_tasks
            WHERE task_type = 'CLOUD FOUNDRY' AND enabled = 'Y'
        """,
            fetch=True,
            dict_cursor=True,
        )

        tasks = [row["task_name"] for row in rows]
        return (
            "\n".join([f"<li>{task}</li>" for task in tasks])
            if rows
            else "No Cloud Foundry operations found."
        )

    except Exception as e:
        return f"Unexpected Error: {str(e)}"


def is_application_available_to_user(
    user_id: str,
    group_name: str,
    cf_app_name: str,
) -> bool:
    log.info(
        "Executing is_application_available_to_user",
        user_id=user_id,
        group_name=group_name,
        cf_app_name=cf_app_name,
    )

    try:
        result = db.execute_query(
            """
            SELECT COUNT(1) AS cnt
            FROM public.chatops_users a
            JOIN public.chatops_app_groups b ON a.group_name = b.group_name
            WHERE LOWER(a.userid) = LOWER(%s)
            AND LOWER(a.group_name) = LOWER(%s)
            AND LOWER(%s) LIKE '%%' || LOWER(b.application) || '%%'            
            """,
            (user_id, group_name, cf_app_name),
            dict_cursor=True,
        )

        count = result[0]["cnt"] if result else 0
        return count > 0

    except Exception as e:
        log.error("Error checking application access", error=str(e))
        return False
