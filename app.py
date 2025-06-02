import streamlit as st
import structlog
import sys
from io import StringIO
from backend.utilities import DualOutput
from auth.authentication_handler import Authenticator
from frontend.chat_window import ChatWindow
from frontend.chat_sidebar import ChatSidebar
from backend.knowledge_base import (
    get_cf_agent_context,
    get_ira_agent_context,
)  # Assuming path is correct
from backend.utilities import get_llm
from agents.cloud_foundry_agent import CfAgent
from agents.ira_agent import IraAgent
from core.config import settings

# Initialize logger
log = structlog.get_logger()

# --- Persistent log_stream using st.session_state ---
if "log_stream" not in st.session_state:
    st.session_state.log_stream = StringIO()
    log.info("Initialized new log_stream in session_state.")
# Always use the log_stream from session_state for this run
current_log_stream = st.session_state.log_stream
# --- End Persistent log_stream ---


# --- DualOutput and stdout redirection ---
# This needs to use the persistent log_stream from session_state.
if "stdout_redirected_to_session_stream" not in st.session_state:
    original_stdout = sys.__stdout__
    # Create DualOutput with the session's log_stream
    # Store the DualOutput handler in session state to check its identity later if needed
    st.session_state.dual_output_handler = DualOutput(
        original_stdout, current_log_stream
    )
    sys.stdout = st.session_state.dual_output_handler
    st.session_state.stdout_redirected_to_session_stream = True
    log.info(
        "Stdout redirected to DualOutput with session_state log_stream for the first time."
    )
else:
    # On subsequent reruns, ensure sys.stdout is still our correct DualOutput instance.
    # This check assumes DualOutput stores its StringIO stream as self.stream2
    if not (
        isinstance(sys.stdout, DualOutput)
        and hasattr(sys.stdout, "stream2")
        and sys.stdout.stream2 == current_log_stream
    ):
        log.warning(
            "sys.stdout was not the correct DualOutput instance or not using session_state log_stream. Re-redirecting."
        )
        original_stdout = sys.__stdout__
        st.session_state.dual_output_handler = DualOutput(
            original_stdout, current_log_stream
        )
        sys.stdout = st.session_state.dual_output_handler
# --- End DualOutput setup ---


# Initialize UI and Authenticator (passing the persistent log_stream)
authenticator = Authenticator()
# Pass the persistent log_stream from session_state
chat_window = ChatWindow(log_stream=current_log_stream)
chat_sidebar = ChatSidebar(log_stream=current_log_stream)


def main():
    log.info("Initializing Streamlit application in main().")
    st.set_page_config(page_title="ContextTesting", layout="wide")

    # --- MODAL STATE INITIALIZATION ---
    if "show_suggestion_modal" not in st.session_state:
        st.session_state.show_suggestion_modal = False
    if "current_suggestion_to_edit" not in st.session_state:
        st.session_state.current_suggestion_to_edit = ""
    if "injected_user_message" not in st.session_state:
        st.session_state.injected_user_message = None
    # --- END MODAL STATE INITIALIZATION ---

    is_authenticated, result, user_id = authenticator.authenticate_user()

    if is_authenticated:
        log.info("User authenticated successfully.", user_id=user_id)

        # Initialize other session states (user, LLM, chat history, etc.)
        if "user_id" not in st.session_state:
            st.session_state.user_id = user_id
        if "user_name" not in st.session_state:
            st.session_state.user_name = result
        if "ui_context" not in st.session_state:
            st.session_state.ui_context = "CF"
        if "selected_llm_name" not in st.session_state:
            st.session_state.selected_llm_name = "llama-3.3-70b-versatile"
        if "llm_temperature" not in st.session_state:
            st.session_state.llm_temperature = 0.7

        if "agent_needs_reinit" not in st.session_state:
            st.session_state.agent_needs_reinit = False

        if "llm" not in st.session_state or st.session_state.get("agent_needs_reinit"):
            st.session_state.llm = get_llm(
                st.session_state.selected_llm_name, st.session_state.llm_temperature
            )
            log.info(
                f"LLM Initialized/Re-initialized with {st.session_state.selected_llm_name}."
            )

        if "chat_agent" not in st.session_state:
            st.session_state.chat_agent = None

        if "OPENAI_API_KEY" not in st.session_state:
            st.session_state.OPENAI_API_KEY = settings.OPENAI_API_KEY
        if "GROQ_API_KEY" not in st.session_state:
            st.session_state.GROQ_API_KEY = settings.GROQ_API_KEY

        for key in ["chat_history_cf", "chat_history_ira", "chat_history_direct"]:
            if key not in st.session_state:
                st.session_state[key] = []

        if "suggested_prompts" not in st.session_state:
            st.session_state.suggested_prompts = []

        log.info("Render the Chatbot UI parts.")

        chat_sidebar.ui_context_selector()
        current_ui_context = st.session_state.ui_context
        chat_sidebar.show_suggestions()
        
        if current_ui_context in ["CF", "IRA"]:
            chat_sidebar.show_agent_logs()
        chat_sidebar.show_llm_selection()

        if current_ui_context == "CF":
            if not isinstance(
                st.session_state.get("chat_agent"), CfAgent
            ) or st.session_state.get("agent_needs_reinit", False):
                if st.session_state.llm:
                    log.info("Initializing/Re-initializing CfAgent.")
                    st.session_state.chat_agent = CfAgent()
                else:
                    log.warning("LLM not available for CfAgent initialization.")
            if st.session_state.chat_agent:
                chat_window.show_agent_window(
                    get_cf_agent_context(), "chat_history_cf", "cf_chat_input_key"
                )

        elif current_ui_context == "IRA":
            if not isinstance(
                st.session_state.get("chat_agent"), IraAgent
            ) or st.session_state.get("agent_needs_reinit", False):
                if st.session_state.llm:
                    log.info("Initializing/Re-initializing IraAgent.")
                    st.session_state.chat_agent = IraAgent()
                else:
                    log.warning("LLM not available for IraAgent initialization.")
            if st.session_state.chat_agent:
                chat_window.show_agent_window(
                    get_ira_agent_context(), "chat_history_ira", "ira_chat_input_key"
                )
        else:  # DIRECT
            st.session_state.chat_agent = None
            chat_window.show_direct_window("direct_chat_input_key")

        st.session_state.agent_needs_reinit = False  # Reset flag after potential use

    else:
        login_url = result
        log.warning("User not authenticated. Showing login.")
        st.write("Click the button below to log in with Azure AD:")
        st.markdown(
            f"""<a href="{login_url}" target="_self" style="display:inline-block; background-color:#4CAF50; color:white; padding:10px 20px; text-align:center; text-decoration:none; border-radius:5px;">Log in with Azure AD</a>""",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
