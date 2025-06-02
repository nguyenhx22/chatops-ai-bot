import streamlit as st
from backend.knowledge_base import (
    get_cf_agent_context,
    get_ira_agent_context,
    get_cloud_foundry_app_info,
    get_application_groups,
    get_cloud_foundry_tasks,
    is_application_available_to_user
)



########## Test knowledge_base()
st.session_state.user_id = "hnguye005"

# results = get_cf_agent_context()
# print(results)

# results2 = get_ira_agent_context()
# print(results2)

# results3 = get_cloud_foundry_app_info("npp-chatops-e2e-service#34545fg")
# print(results3)


# results5 = get_cloud_foundry_tasks()
# print(results5)


user_permission = is_application_available_to_user(
                user_id=st.session_state.user_id,
                group_name="npp",
                cf_app_name="npp-chatops-e2e-service",
            )
print(f"User permission for application: {user_permission}")