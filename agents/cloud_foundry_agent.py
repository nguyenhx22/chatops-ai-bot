import streamlit as st
import structlog
from typing import Type # Keep Type if used by other parts of your actual code
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain.tools.render import render_text_description
from agents.tools.cloud_foundry_tools import ( # Assuming this import path is correct
    CloudFoundryTools,
    GetAppInfoInput,
    RestartAppInput,
    StartAppInput,
    StopAppInput,
    CheckHealthAppInput
)
import os # For path manipulation

log = structlog.get_logger()

# --- Helper function to load the prompt (remains the same) ---
def load_prompt_from_file(file_path: str) -> str:
    """Loads a prompt template from a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log.error(f"Prompt file not found at {file_path}")
        # Consider if the application should stop or use a default fallback prompt
        raise
    except Exception as e:
        log.error(f"Error loading prompt from {file_path}: {e}")
        raise

class CfAgent:
    def __init__(self):
        """
        Initializes the Cloud Foundry Agent using create_openai_tools_agent
        and StructuredTool for robust handling of tool arguments.
        The system prompt is loaded from a fixed path relative to this file.
        """
        log.info("Instantiating Cloud Foundry Agent using StructuredTool.")
        print("\nInstantiating Cloud Foundry Agent (using StructuredTool)\n")

        try:
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_file_path = "agents/prompts/cf_agent_system_prompt.txt"
            log.info(f"Resolved prompt file path: {prompt_file_path}")

        except Exception as e:
            log.error(f"Error determining prompt file path: {e}")
            raise RuntimeError(f"Could not determine prompt file path: {e}")


        # 1. Define Tools using StructuredTool.from_function
        self.tools = [
            StructuredTool.from_function(
                func=CloudFoundryTools.get_application_information,
                name="get_application_information",
                description="Tool used to retrieve the required information for Cloud Foundry tasks, such as cf_organization and cf_space, for a given application.",
                args_schema=GetAppInfoInput,
            ),
            StructuredTool.from_function(
                func=CloudFoundryTools.restart_application,
                name="restart_application",
                description=(
                    "This tool is used to restart an application in Cloud Foundry. "
                    "Before executing, confirm user has specify the Cloud Foundry site, if not ask for it. "
                    "Before executing, confirm the user's intent by asking for confirmation (e.g., 'Are you sure?'). "
                    "Proceed only if the user replies affirmatively ('yes', 'confirm', etc.). "
                    "The get_application_information tool MUST be executed first in the conversation flow to retrieve required info like 'cf_organization' and 'cf_space'. "
                    "Input MUST contain 'group_name', 'application', 'cloud_foundry_site', 'cf_organization', and 'cf_space'."
                ),
                args_schema=RestartAppInput,
            ),
            # ... (other tools remain the same) ...
            StructuredTool.from_function(
                func=CloudFoundryTools.start_application,
                name="start_application",
                description=(
                    "This tool is used to start an application in Cloud Foundry. "
                    "Before executing, confirm user has specify the Cloud Foundry site, if not ask for it. "
                    "Before executing, confirm the user's intent by asking for confirmation (e.g., 'Are you sure?'). "
                    "Proceed only if the user replies affirmatively ('yes', 'confirm', etc.). "
                    "The get_application_information tool MUST be executed first in the conversation flow to retrieve required info like 'cf_organization' and 'cf_space'. "
                    "Input MUST contain 'group_name', 'application', 'cloud_foundry_site', 'cf_organization', and 'cf_space'."
                ),
                args_schema=StartAppInput,
            ),
            StructuredTool.from_function(
                func=CloudFoundryTools.stop_application,
                name="stop_application",
                description=(
                    "This tool is used to stop an application in Cloud Foundry. "
                    "Before executing, confirm user has specify the Cloud Foundry site, if not ask for it. "
                    "Before executing, confirm the user's intent by asking for confirmation (e.g., 'Are you sure?'). "
                    "Proceed only if the user replies affirmatively ('yes', 'confirm', etc.). "
                    "The get_application_information tool MUST be executed first in the conversation flow to retrieve required info like 'cf_organization' and 'cf_space'. "
                    "Input MUST contain 'group_name', 'application', 'cloud_foundry_site', 'cf_organization', and 'cf_space'."
                ),
                args_schema=StopAppInput,
            ),
            StructuredTool.from_function(
                func=CloudFoundryTools.check_application_health,
                name="check_application_health",
                description=(
                    "Use this tool when the user asks about the health of an application. "
                    "This tool is used to check the health of an application in Cloud Foundry. "
                    "Before executing, confirm user has specify the Cloud Foundry site, if not ask for it. "
                    "The get_application_information tool MUST be executed first in the conversation flow to retrieve required info like 'cf_organization' and 'cf_space'. "
                    "Input MUST contain 'group_name', 'application', 'cloud_foundry_site', 'cf_organization', and 'cf_space'."
                ),
                args_schema=CheckHealthAppInput,
            ),
        ]

        # 2. Load and Create Prompt Template
        self.rendered_tools = render_text_description(self.tools)
        system_message_template = load_prompt_from_file(prompt_file_path)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message_template),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        log.info("Prompt template loaded successfully.", prompt_file_path=prompt_file_path)

        # 3. Create the Agent
        if "llm" not in st.session_state:
            log.error("LLM not found in st.session_state. Please initialize it before CfAgent.")
            raise ValueError("LLM not initialized in st.session_state. Ensure st.session_state.llm is set.")

        self.agent = create_openai_tools_agent(
            st.session_state.llm, self.tools, self.prompt
        )

        # 4. Create the Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )
        log.info(f"Cloud Foundry Agent initialized successfully using internal prompt: {prompt_file_path}")

    def interact(self, user_input: str, context: str) -> str:
        """
        Handles interaction with the agent using AgentExecutor.invoke.
        """
        log.info("Interacting with the CfAgent executor.", user_input=user_input)

        if self.agent_executor is None:
            log.error("Agent executor not initialized.")
            return (
                "Error: Agent is not properly initialized. Please check configuration."
            )

        chat_history = st.session_state.get("chat_history_cf", [])
        log.debug(f"Using chat history from session state: {chat_history}")

        try:
            response = self.agent_executor.invoke(
                {
                    "input": user_input,
                    "context_json": context,
                    "rendered_tools": self.rendered_tools,
                    "chat_history": chat_history,
                }
            )
            output = response.get("output", "Sorry, I didn't get a valid response.")
            log.info("AgentExecutor response generated.", response=output)
            return output

        except Exception as e:
            error_message = str(e).lower()
            if (
                "invalid api key" in error_message
                or "authentication" in error_message
                or "unauthorized" in error_message
            ):
                log.error("Invalid API Key detected during interaction", error=str(e))
                return f"🔑 Invalid API Key. Please check your API Key in the sidebar settings. Error: {error_message}"
            else:
                log.error(
                    "Unexpected error during CfAgent interaction",
                    error=str(e),
                    exc_info=True,
                )
                return f"⚠️ Unexpected error occurred: {error_message}. Please check the logs or try again later."
