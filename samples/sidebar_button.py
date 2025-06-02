import streamlit as st
import requests
from frontend.style import BUTTON_STYLES

# Dummy API URL (Replace with actual API endpoint)
API_URL = "https://jsonplaceholder.typicode.com/posts"

# Inject CSS
st.markdown(BUTTON_STYLES, unsafe_allow_html=True)

st.title("Chatbot with Sidebar Buttons")

user_message = st.chat_input("Ask something or choose an action...")

if user_message:
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        st.write("Please choose an action from the sidebar:")

# Place buttons in the sidebar
st.sidebar.title("Actions")
action1 = st.sidebar.button("Action 1")
action2 = st.sidebar.button("Action 2")

if action1:
    with st.chat_message("user"):
        st.write("I chose **Action 1**")

    with st.chat_message("assistant"):
        st.write("Processing **Action 1**... ⏳")
        response = requests.post(API_URL, json={"action": "Action 1"})
        if response.status_code == 201:
            st.success("✅ Action 1 executed successfully!")
        else:
            st.error("❌ Action 1 failed!")

if action2:
    with st.chat_message("user"):
        st.write("I chose **Action 2**")

    with st.chat_message("assistant"):
        st.write("Processing **Action 2**... ⚡")
        response = requests.post(API_URL, json={"action": "Action 2"})
        if response.status_code == 201:
            st.success("✅ Action 2 executed successfully!")
        else:
            st.error("❌ Action 2 failed!")
