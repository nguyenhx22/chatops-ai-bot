import structlog
from pydantic import BaseModel, Field
from typing import Type

log = structlog.get_logger()

# --- Input Schema for AskHuman Tool ---
class AskHumanInput(BaseModel):
    """Input schema for the ask_human tool."""
    question: str = Field(description="The specific question to ask the human user for clarification, confirmation, or subjective input.")

# --- Tool Function for AskHuman ---
def ask_human_tool_func(question: str) -> str:
    """
    This function is called by the AskHuman tool.
    It signals to the calling application (Streamlit) that human input is needed
    by returning a specially formatted string.
    The AgentExecutor should ideally handle this directly if the tool has return_direct=True,
    or the calling application needs to check for this specific output format.
    """
    log.info("AskHuman tool invoked.", question_to_human=question)
    # The special string format to signal interruption
    return f"HUMAN_INPUT_REQUIRED::{question}"
