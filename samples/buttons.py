import streamlit as st
import requests

# Dummy API URL (Replace with actual API endpoint)
API_URL = "https://jsonplaceholder.typicode.com/posts"

st.markdown("""
<style>
body {
    background-color: #EAEAEA;
}

.button-container {
    display: flex;
    justify-content: flex-start;
    gap: 3px;
}
div.stButton > button {
    background-color: #2DAA9E;
    color: #FFFFFF;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 6px;
    cursor: pointer;
    transition: background 0.3s ease-in-out;
    min-width: 100px;
}
div.stButton > button:hover {
    background-color: #034C53;
}
</style>
""", unsafe_allow_html=True)

st.title("Chatbot with Modern Buttons")

user_message = st.chat_input("Ask something or choose an action...")

if user_message:
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        st.write("Please choose an action below:")

with st.chat_message("assistant"):
    st.write("What would you like to do?")

    button_col1, button_col2, _ = st.columns([0.1, 0.1, 0.4])

    with button_col1:
        action1 = st.button("Action 1")

    with button_col2:
        action2 = st.button("Action 2")

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
