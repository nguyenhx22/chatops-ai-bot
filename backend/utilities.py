import streamlit as st
import re, os, json
import structlog
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from core.config import settings

# Initialize logger
log = structlog.get_logger()

class DualOutput(object):
    def __init__(self, console, buffer):
        self.console = console
        self.buffer = buffer
        log.debug("DualOutput initialized.")

    def write(self, data):
        log.debug("Writing data to both console and buffer.")
        self.console.write(data)
        self.buffer.write(data)

    def flush(self):
        log.debug("Flushing console and buffer.")
        self.console.flush()
        self.buffer.flush()

def ansi_to_html(text):
    """Convert ANSI escape sequences to HTML."""
    log.debug("Converting ANSI to HTML.")
												  
    ansi_to_html_map = {
        r"\x1B\[1m": "<b>",  # Bold
        r"\x1B\[32;1m": '<span style="color:green; font-weight:bold;">',  # Bright Green Bold
        r"\x1B\[33;1m": '<span style="color:blue; font-weight:bold;">',  # Bright Blue Bold
        r"\x1B\[36;1m": '<span style="color:purple; font-weight:bold;">',  # Bright purple Bold
        r"\x1B\[34;1m": '<span style="color:blue; font-weight:bold;">',  # Brighter Blue Bold
        r"\x1B\[0m": "</span></b>",  # Reset
        r"\x1B\[1;3m": "<i>",  # Italic
        r"\x1B\[1;3m": "</i>",  # Close Italic
    }

    for ansi, html in ansi_to_html_map.items():
        text = re.sub(ansi, html, text)

    text = text.replace("[0m", "</span></b>")
    log.debug("ANSI conversion completed.")
    return text

def get_llm(llm="OpenAI gpt-4", temperature=0.5):
    """Get the selected_llm model."""
    log.info("Fetching LLM model.", selected_llm=llm, temperature=temperature)

    # Grab API keys from Streamlit session state or fallback to env vars
    openai_key = st.session_state.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    groq_key = st.session_state.get("GROQ_API_KEY", settings.GROQ_API_KEY)

    try:
        if llm == "OpenAI gpt-4":
            selected_llm = ChatOpenAI(api_key=openai_key, model="gpt-4", temperature=temperature)
        elif llm == "OpenAI gpt-4o-mini":
            selected_llm = ChatOpenAI(api_key=openai_key, model="gpt-4o-mini", temperature=temperature)
        elif llm == "OpenAI gpt-3.5-turbo":
            selected_llm = ChatOpenAI(api_key=openai_key, model="gpt-3.5-turbo", temperature=temperature)
        elif llm == "llama-3.3-70b-versatile":
            selected_llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile", temperature=temperature)
        elif llm == "llama3-70b-8192":
            selected_llm = ChatGroq(api_key=groq_key, model="llama3-70b-8192", temperature=temperature)
        else:
            selected_llm = ChatOpenAI(api_key=openai_key, model="gpt-4", temperature=0.5)
            log.warning("LLM model not recognized, defaulting to GPT-4.")

        log.info("Successfully initialized LLM.", model=llm)
        return selected_llm

    except Exception as e:
        log.error("Error initializing LLM.", error=str(e))
        return None


