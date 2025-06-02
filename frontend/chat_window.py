# frontend/chat_window.py
import streamlit as st
import structlog
import os, json, platform 
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from agents.prompt_suggester import PromptSuggester

log = structlog.get_logger()

class ChatWindow:

    def __init__(self, log_stream=None):
        log.info("Initializing ChatWindow")
        self.system = platform.system()
        log.info(f"Detected system platform: {self.system}")
        if self.system not in ("Windows", "Darwin"):
            self._configure_proxy_from_cf()
        self.log_stream = log_stream

    def _configure_proxy_from_cf(self): 
        vcap_services = os.environ.get("VCAP_SERVICES")
        if vcap_services:
            try:
                services = json.loads(vcap_services)
                proxy_service = services.get("c-proxy", [{}])[0]
                credentials = proxy_service.get("credentials", {})
                proxy_uri = credentials.get("uri")
                if proxy_uri:
                    os.environ["http_proxy"] = proxy_uri
                    os.environ["https_proxy"] = proxy_uri
                    log.info("Proxy configured from Cloud Foundry environment", proxy_uri=proxy_uri)
                else:
                    log.warning("Proxy URI not found in credentials")
            except Exception as e:
                log.error("Error parsing VCAP_SERVICES or setting proxy", error=str(e))
        else:
            log.info("VCAP_SERVICES environment variable not found. Skipping proxy config.")

    def _render_conversation(self, history_key: str, input_key: str, input_label: str, handle_response_fn):
        if history_key not in st.session_state:
            st.session_state[history_key] = [AIMessage(content="Hello, I am a bot. How can I help you?")]

        # 1. Display chat messages
        for msg in st.session_state[history_key]:
            role = "ai" if isinstance(msg, AIMessage) else "human" 
            with st.chat_message(role): 
                st.write(str(msg.content)) 

        processed_input_this_run = None

        # 2. Process injected message (from modal's submit)
        if st.session_state.get("injected_user_message"): 
            processed_input_this_run = st.session_state.pop("injected_user_message")
            log.info(f"Processing injected message for {history_key}: {processed_input_this_run}")
            if st.session_state.get("show_suggestion_modal", False):
                st.session_state.show_suggestion_modal = False
                st.session_state.current_suggestion_to_edit = ""

        # 3. Modal-like container for editing suggestions
        if st.session_state.get("show_suggestion_modal", False):
            with st.container():
                st.markdown("---") 
                st.subheader("✏️ Edit Suggested Prompt")
                
                modal_text_area_key = f"{history_key}_modal_edit_text_area"
                current_text_for_modal = st.session_state.get("current_suggestion_to_edit", "")
                
                edited_text_from_modal = st.text_area(
                    "Edit prompt below:", 
                    value=current_text_for_modal, 
                    key=modal_text_area_key,
                    height=100
                )

                col1, col2, col_spacer = st.columns([1, 1, 2]) 
                with col1:
                    if st.button("Submit Change", key=f"{history_key}_modal_submit_btn", use_container_width=True):
                        st.session_state.injected_user_message = edited_text_from_modal 
                        st.session_state.show_suggestion_modal = False 
                        st.session_state.current_suggestion_to_edit = "" 
                        st.rerun() 
                with col2:
                    if st.button("Cancel", key=f"{history_key}_modal_cancel_btn", use_container_width=True):
                        st.session_state.show_suggestion_modal = False 
                        st.session_state.current_suggestion_to_edit = "" 
                        st.rerun() 
                st.markdown("---")

        # 4. Regular chat input (st.chat_input)
        chat_input_is_disabled = st.session_state.get("show_suggestion_modal", False)
        
        if not processed_input_this_run:
            # input_key here is the one passed from show_agent_window/show_direct_window
            direct_chat_input_value = st.chat_input(input_label, key=input_key, disabled=chat_input_is_disabled)
            if direct_chat_input_value: 
                processed_input_this_run = direct_chat_input_value
                log.info(f"Processing user typed message from chat_input for {history_key}: {processed_input_this_run}")
        elif chat_input_is_disabled : 
             st.chat_input(input_label, key=input_key, disabled=True)


        # 5. Process the determined input
        if processed_input_this_run:
            st.session_state[history_key].append(HumanMessage(content=processed_input_this_run))
            
            with st.chat_message("ai"): 
                with st.spinner("Processing..."):
                    try:
                        response = handle_response_fn(processed_input_this_run)
                    except Exception as e:
                        log.error(f"Error in handle_response_fn for {history_key}", error=str(e), exc_info=True)
                        response = f"⚠️ An error occurred: {str(e)}"
                    st.write(response)
            st.session_state[history_key].append(AIMessage(content=response))
            
            if st.session_state.get("llm"):
                try:
                    suggester = PromptSuggester(llm=st.session_state.llm)
                    st.session_state.suggested_prompts = suggester.generate()
                except Exception as e:
                    log.warning("Failed to refresh suggestions post-interaction", error=str(e))           
            st.rerun() 

    # Updated signature to accept input_widget_key
    def show_agent_window(self, chat_context: str, history_key: str, input_widget_key: str):
        log.info(f"Rendering agent chat window for {history_key}", user=st.session_state.get("user_name", ("Unknown", ""))[0])
        user_id_tuple_safe = st.session_state.get("user_id", ("N/A",""))
        user_id_display = user_id_tuple_safe[0] if isinstance(user_id_tuple_safe, tuple) else user_id_tuple_safe

        st.markdown(
            f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
                <h2 style="color: #2E3A87; font-size: 1.8em; margin-bottom: 5px;">🤖 ChatOps-AI&nbsp;&nbsp;&nbsp;(User:&nbsp;{user_id_display})</h2>
                <p style="color: #495B8E; font-size: 13px; margin-top: 0;">
                    An AI-driven chatbot powered by intelligent agents for managing production operations.
                </p>
            </div>""", unsafe_allow_html=True)

        def handle_agent_response(user_input):
            log.info("Handling agent response", user_input=user_input)
            agent = st.session_state.get("chat_agent")
            if agent:
                return agent.interact(user_input=user_input, context=chat_context)
            return "⚠️ Chat agent not available."
        # Pass input_widget_key as input_key to _render_conversation
        self._render_conversation(history_key, input_widget_key, "Type your message here...", handle_agent_response)

    # Updated signature to accept input_widget_key
    def show_direct_window(self, input_widget_key: str): 
        history_key="chat_history_direct"
        log.info(f"Rendering direct chat window for {history_key}", user=st.session_state.get("user_name", ("Unknown", ""))[0])
        user_id_tuple_safe = st.session_state.get("user_id", ("N/A",""))
        user_id_display = user_id_tuple_safe[0] if isinstance(user_id_tuple_safe, tuple) else user_id_tuple_safe

        st.markdown(
            f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
                <h2 style="color: #2E3A87; font-size: 1.8em; margin-bottom: 5px;">🤖 ChatOps-AI&nbsp;&nbsp;&nbsp;(User:&nbsp;{user_id_display})</h2>
                <p style="color: #495B8E; font-size: 13px; margin-top: 0;">
                    Chatbot (Non-Agent Mode) - This chatbot is used to directly talk to the pre-trained model. (Context: DIRECT)
                </p>
            </div>""", unsafe_allow_html=True)

        def handle_direct_response(user_input):
            try:
                stream = self._get_direct_response(user_input, st.session_state.get(history_key, []))
                full_response = "".join(list(stream))
                if not full_response.strip(): # Check if response is empty or just whitespace
                    log.warning("Direct LLM response was empty.")
                    return "🤔 The LLM returned an empty response. Please try rephrasing."
                return full_response
            except Exception as e:
                error_message = str(e).lower()
                if "api key" in error_message or "authentication" in error_message or "unauthorized" in error_message:
                    log.error("Invalid API Key detected", error=str(e), exc_info=True) # Add exc_info
                    return f"🔑 Invalid API Key. Please check your API Key in the sidebar settings. Error: {error_message}"
                else:
                    log.error("Unexpected error in direct response", error=str(e), exc_info=True) # Add exc_info
                    return f"⚠️ Unexpected error: {error_message}"
        # Pass input_widget_key as input_key to _render_conversation
        self._render_conversation(history_key, input_widget_key, "Type your message here...", handle_direct_response)

    def _get_direct_response(self, user_input: str, chat_history: list): 
        template = """
        You are a helpful assistant. Answer the following questions considering the history of the conversation:
        Chat history: {chat_history_str}
        User Input: {user_input}
        """ 
        
        simple_history_str = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {str(msg.content)}" 
            for msg in chat_history[-6:] 
        ])

        prompt = ChatPromptTemplate.from_template(template)
        llm = st.session_state.get("llm")
        if not llm:
            log.error("LLM not found in session state for direct response.")
            yield "⚠️ LLM is not available. Please check configuration." 
            return

        try:
            chain = prompt | llm | StrOutputParser()
            log.info("Streaming direct response from LLM for user input.") # Log before streaming
            for chunk in chain.stream({
                "chat_history_str": simple_history_str, 
                "user_input": user_input,
            }):
                yield chunk
            log.info("Finished streaming direct response from LLM.") # Log after successful stream
        except Exception as e:
            log.error("Error during LLM stream for direct response", error=str(e), exc_info=True)
            yield f"⚠️ Error communicating with LLM: {str(e)}"