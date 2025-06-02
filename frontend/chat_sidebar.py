import streamlit as st
import structlog
from backend.utilities import ansi_to_html, get_llm
from agents.cloud_foundry_agent import CfAgent
from agents.ira_agent import IraAgent
from agents.prompt_suggester import PromptSuggester


log = structlog.get_logger()


class ChatSidebar:
    def __init__(self, log_stream=None):
        self.log_stream = log_stream
        log.info("ChatSidebar initialized")

        # Initialize session state for suggestions if not already done by app.py
        if "suggested_prompts" not in st.session_state:
            st.session_state.suggested_prompts = []
        
        # Modal-related states are primarily managed/initialized in app.py
        # but good to ensure they exist if sidebar tries to interact before app.py fully runs once.
        if "show_suggestion_modal" not in st.session_state:
            st.session_state.show_suggestion_modal = False
        if "current_suggestion_to_edit" not in st.session_state:
            st.session_state.current_suggestion_to_edit = ""

    def show_llm_selection(self):
        log.info("Rendering LLM selection sidebar")
        with st.sidebar:
            st.markdown("---")
            st.markdown("<h3 style=\"color: #2E3A87;\">🧠 Select LLM Model:</h3>", unsafe_allow_html=True)

            llm_options = [
                "OpenAI gpt-4", "OpenAI gpt-4o-mini", "OpenAI gpt-3.5-turbo",
                "llama-3.3-70b-versatile", "llama3-70b-8192",
            ]
            default_llm_name = "llama-3.3-70b-versatile"

            current_selected_llm_name = st.session_state.get("selected_llm_name", default_llm_name)
            try:
                current_index = llm_options.index(current_selected_llm_name)
            except ValueError:
                current_index = llm_options.index(default_llm_name)
                st.session_state.selected_llm_name = default_llm_name

            selected_llm_name = st.radio(
                "Choose a model:", options=llm_options, index=current_index, key="llm_radio_key_sidebar"
            )

            current_llm_temp = st.session_state.get("llm_temperature", 0.7)
            temp = st.slider(
                "LLM Temperature:", min_value=0.0, max_value=1.0, value=current_llm_temp, step=0.1, key="llm_temp_key_sidebar"
            )

            st.markdown("---")
            st.markdown("<h3 style=\"color: #2E3A87;\">🗝️ LLM API Keys - Override:</h3>", unsafe_allow_html=True)

            current_openai_key = st.session_state.get("OPENAI_API_KEY", "")
            openai_key_input = st.text_input(
                "OPENAI_API_KEY", value=current_openai_key, type="password", key="openai_key_input_sidebar_key"
            )
            current_groq_key = st.session_state.get("GROQ_API_KEY", "")
            groq_key_input = st.text_input(
                "GROQ_API_KEY (Llama Models)", value=current_groq_key, type="password", key="groq_key_input_sidebar_key"
            )

            llm_config_changed = False
            if selected_llm_name != st.session_state.selected_llm_name: # Check against current session state
                st.session_state.selected_llm_name = selected_llm_name
                llm_config_changed = True
            if temp != st.session_state.llm_temperature: # Check against current session state
                st.session_state.llm_temperature = temp
                llm_config_changed = True
            if openai_key_input != st.session_state.OPENAI_API_KEY: # Check against current session state
                 st.session_state.OPENAI_API_KEY = openai_key_input
                 llm_config_changed = True
            if groq_key_input != st.session_state.GROQ_API_KEY: # Check against current session state
                 st.session_state.GROQ_API_KEY = groq_key_input
                 llm_config_changed = True

            if llm_config_changed:
                log.info("LLM configuration changed. Re-initializing LLM and setting agent re-init flag.")
                st.session_state.llm = get_llm(
                    st.session_state.selected_llm_name, 
                    st.session_state.llm_temperature
                )
                # Flag for app.py to re-initialize agents
                st.session_state.agent_needs_reinit = True 
                st.rerun()


    def show_agent_logs(self): 
        # Show logs only for CF and IRA contexts and if log_stream is provided
        if self.log_stream and st.session_state.get("ui_context") in ["CF", "IRA"]:
            log.info("Rendering agent logs")
            with st.sidebar:
                st.markdown("---")
                st.markdown("<h3 style=\"color: #2E3A87;\">📜 AI Agent Logs:</h3>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9;'>{ansi_to_html(self.log_stream.getvalue())}</div>",
                    unsafe_allow_html=True
                )

    def ui_context_selector(self) -> str: 
        log.info("Rendering ui_context_selector")
        with st.sidebar:
            st.markdown("<h3 style=\"color: #2E3A87;\">🤖 ChatOps Context Selector:</h3>", unsafe_allow_html=True)
            options = {
                "☁️ Cloud Foundry (CF)": "CF",
                "🕵️ Incident Resolution Assistant (IRA)": "IRA",
                "🚫 No Context (DIRECT)": "DIRECT",
            }
            labels = list(options.keys())
            
            current_context_val = st.session_state.get("ui_context", "CF") # Default if not set
            try:
                current_label = next(k for k, v in options.items() if v == current_context_val)
            except StopIteration: 
                current_label = labels[0] # Fallback to first option
                st.session_state.ui_context = options[current_label]


            selected_label = st.selectbox("Choose context:", options=labels, index=labels.index(current_label), key="ui_context_selectbox_key")
            selected_ui_context = options[selected_label]

            if selected_ui_context != st.session_state.ui_context: # Use current session state for comparison
                log.info(f"UI context changed from {st.session_state.ui_context} to {selected_ui_context}")
                st.session_state.ui_context = selected_ui_context
                
                # --- Reset modal state on context change ---
                st.session_state.show_suggestion_modal = False
                st.session_state.current_suggestion_to_edit = ""
                st.session_state.injected_user_message = None 
                # --- End reset modal state ---
                st.session_state.agent_needs_reinit = True # Flag for agent re-init on context change

                if st.session_state.get("llm"): 
                    suggester = PromptSuggester(llm=st.session_state.llm)
                    st.session_state.suggested_prompts = suggester.generate()
                else:
                    st.session_state.suggested_prompts = ["LLM not ready. Please check settings."]
                st.rerun()
            return st.session_state.ui_context # Return current context from session state

    def show_suggestions(self): 
        # Only show suggestions if not in DIRECT mode and LLM is available
        if st.session_state.get("ui_context") == "DIRECT" or not st.session_state.get("llm"):
            return

        with st.sidebar:
            st.markdown("---")
            st.markdown("<h3 style=\"color: #2E3A87;\">💡 AI Suggested Prompts:</h3>", unsafe_allow_html=True)

            # Generate suggestions if not already present (e.g., on first load or after context change)
            if not st.session_state.get("suggested_prompts"):
                if st.session_state.get("llm"):
                    suggester = PromptSuggester(llm=st.session_state.llm)
                    st.session_state.suggested_prompts = suggester.generate()
                else:
                    st.session_state.suggested_prompts = ["LLM not ready for suggestions."]


            if st.button("🔄 Refresh Suggestions", key="refresh_suggestions_sidebar_button_main_key"):
                st.session_state.show_suggestion_modal = False 
                st.session_state.current_suggestion_to_edit = ""
                if st.session_state.get("llm"):
                    suggester = PromptSuggester(llm=st.session_state.llm)
                    st.session_state.suggested_prompts = suggester.generate()
                    st.toast("New suggestions generated!")
                else:
                    st.toast("LLM not available to generate suggestions.")
                st.rerun() 

            suggestions_list = st.session_state.get("suggested_prompts", [])
            
            for i, prompt_text in enumerate(suggestions_list):
                # Ensure unique keys for suggestion buttons
                if st.button(f"👉 {prompt_text}", key=f"sidebar_suggest_prompt_btn_main_key_{i}"):
                    # --- MODAL TRIGGER LOGIC ---
                    st.session_state.current_suggestion_to_edit = prompt_text
                    st.session_state.show_suggestion_modal = True # Flag for chat_window
                    # --- END MODAL TRIGGER LOGIC ---
                    st.rerun() # Rerun to allow chat_window to display the modal