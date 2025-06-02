import streamlit as st
import structlog
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain.tools.render import render_text_description
from agents.tools.ira_tools import (
    IRATools,
    GetPlatformInfoInput,
    GetIncidentHistoryInput,
    GetInvestigationHistoryInput
)


log = structlog.get_logger()

class IraAgent:
    def __init__(self):
        """
        Initializes the IRA Agent using create_openai_tools_agent
        and StructuredTool.
        """
        log.info("Instantiating IRA Agent using StructuredTool.")
        print("\nInstantiating IRA Agent (using StructuredTool)\n")

        # 1. Define Tools using StructuredTool.from_function
        self.tools = [
            StructuredTool.from_function(
                func=IRATools.get_platform_information,
                name="get_platform_information",
                description="Retrieves information about a specific IRA platform.",
                args_schema=GetPlatformInfoInput
            ),
            StructuredTool.from_function(
                func=IRATools.get_incident_history,
                name="get_incident_history",
                description="Retrieves historical incident data from IRA.",
                args_schema=GetIncidentHistoryInput # Even if no args, schema helps consistency
            ),
            StructuredTool.from_function(
                func=IRATools.get_investigation_history,
                name="get_investigation_history",
                description="Retrieves historical investigation data from IRA.",
                args_schema=GetInvestigationHistoryInput # Even if no args, schema helps consistency
            ),
        ]

        # 2. Create Prompt Template
        rendered_tools = render_text_description(self.tools)
        SYSTEM_MESSAGE = f"""
        You are an Incident Resolution Assistant (IRA). Your goal is to help users by retrieving information about platforms, incidents, and investigations using the available tools based on the provided context and user requests.

        Context Information (JSON format):
        {{context_json}}

        You have access to the following tools:
        {rendered_tools}

        Follow these instructions carefully:
        - Use the provided `Context Information` if relevant.
        - Use the `get_platform_information` tool when asked for details about a specific platform.
        - Use the `get_incident_history` tool when asked about past incidents.
        - Use the `get_investigation_history` tool when asked about past investigations.
        - If the user asks a general question or a request that doesn't require a specific tool, respond directly based on the conversation history and context.
        - Use the chat history to understand the conversation flow.
        """
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_MESSAGE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 3. Create the Agent
        if "llm" not in st.session_state:
            log.error("LLM not found in session state during IraAgent initialization.")
            st.error("Error: LLM not configured. Please select an LLM in the sidebar.")
            self.agent_executor = None
            return
        llm = st.session_state.llm
        self.agent = create_openai_tools_agent(llm, self.tools, self.prompt)

        # 4. Create the Agent Executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )
        log.info("IRA Agent initialized successfully using StructuredTool.")


    def interact(self, user_input: str, context: str) -> str:
        """
        Handles interaction with the IRA agent using AgentExecutor.invoke.
        Assumes chat history in session state is already correctly formatted.
        """
        log.info("Interacting with the IraAgent executor.", user_input=user_input)

        if self.agent_executor is None:
             log.error("Agent executor not initialized.")
             return "Error: Agent is not properly initialized. Please check configuration."

        chat_history = st.session_state.get("chat_history_ira", [])
        log.debug(f"Using chat history from session state: {chat_history}")

        try:
            # Invoke the agent executor
            response = self.agent_executor.invoke(
                {
                    "input": user_input,
                    "context_json": context,
                    "chat_history": chat_history, # Pass history directly
                }
            )
            output = response.get("output", "Sorry, I didn't get a valid response.")
            log.info("AgentExecutor response generated.", response=output)
            return output

        except Exception as e:
            # Error handling (similar to CfAgent)
            error_message = str(e).lower()
            if "invalid api key" in error_message or "authentication" in error_message or "unauthorized" in error_message:
                log.error("Invalid API Key detected during interaction", error=str(e))
                return f"🔑 Invalid API Key. Please check your API Key in the sidebar settings. Error: {error_message}"
            else:
                log.error("Unexpected error during IraAgent interaction", error=str(e), exc_info=True)
                return f"⚠️ Unexpected error occurred: {error_message}. Please check the logs or try again later."
