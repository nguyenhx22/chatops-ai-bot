import structlog
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
import streamlit as st

log = structlog.get_logger()

class PromptSuggester:
    def __init__(self, llm):
        self.llm = llm

    def generate(self, n=5):
        ui_context = st.session_state.get("ui_context", "DIRECT")

        context_to_history_key = {
            "CF": "chat_history_cf",
            "IRA": "chat_history_ira",
            "DIRECT": "chat_history_direct",
        }

        history_key = context_to_history_key.get(ui_context, "chat_history_direct")
        history = st.session_state.get(history_key, [])

        history_snippets = []
        for message in history[-3:]:
            role = "User" if isinstance(message, HumanMessage) else "Assistant"
            history_snippets.append(f"{role}: {message.content}")

        chat_summary = "\n".join(history_snippets)

        # Include tool documentation per ui_context
        if ui_context == "CF":
            tools_section = """
            - `get_application_information`: Retrieve info about a Cloud Foundry app. Requires `"application"`.
                e.g., "get info for app <app_name>"
            - `restart_application`: Restart a CF app. Requires `"application"`, `"group_name"`, `"cloud_foundry_site"`. Ask for confirmation first.
                e.g., "restart application <app_name> at cf site <cf_site> for the group <group_name>"
            - `start_application`: Start a CF app. Requires `"application"`, `"group_name"`, `"cloud_foundry_site"`. Ask for confirmation first.
                e.g., "start application <app_name> at cf site <cf_site> for the group <group_name>"
            - `stop_application`: Stop a CF app. Requires `"application"`, `"group_name"`, `"cloud_foundry_site"`. Ask for confirmation first.
                e.g., "stop application <app_name> at cf site <cf_site> for the group <group_name>"
            - `check_application_health`: Check health of a CF app. Requires `"application"`, `"group_name"`, `"cloud_foundry_site"`.
                e.g., "check health for application <app_name> at cf site <cf_site> for the group <group_name>"
            """
            
        elif ui_context == "IRA":
            tools_section = """
            - `GetPlatformInformationFromIRA`: Fetch platform information.
            - `get_ira_incident_history`: Retrieve historical incident reports.
            - `get_ira_investigation_history`: Show prior investigations conducted in IRA.
            """
        else:
            tools_section = "None — this is a direct LLM chat without tool access."

        # Prompt including tool documentation
        prompt = ChatPromptTemplate.from_template(
            """
            ### AI Assistant Instructions:
            Based on the available tools and the user's most recent conversation, suggest {n} relevant prompts the user can ask next.
            Only return a list of concise suggestions with no extra commentary.
            Prompts should be a question of a command directed to the AI assistant.

            ### Available Tools:
            {tools_section}

            ### Recent Chat History:
            {chat_summary}

            ### AI Assistant Output Format:
            - If tools are available, the first suggestion should ask about the available tools.
            - if tools are not available, the first suggestion should ask about what the user can do with this chatbot.
            - Provide a list of short one sentence suggestions, each on a new line.
            - Do not use any bullet points or numbering.
            """
        )

        chain = prompt | self.llm | StrOutputParser()

        try:
            suggestions = chain.invoke({
                "n": n,
                "chat_summary": chat_summary,
                "tools_section": tools_section
            })
            return [
                s.strip("-•123. ") for s in suggestions.strip().split("\n") if s.strip()
            ]
        except Exception as e:
            log.warning("LLM suggestion generation failed", error=str(e))
            return [
                "Try asking about what you can do with this chatbot.",
                "Try asking about the available tools."
            ]
