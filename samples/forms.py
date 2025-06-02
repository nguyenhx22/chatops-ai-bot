import streamlit as st
import requests

# API URL (Replace with actual API endpoint)
API_URL = "https://example.com/submit"

st.title("Chatbot with Form Submission")

# Chatbot-like interaction
user_message = st.chat_input("Ask a question or start filling out the form...")

if user_message:
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        st.write("Great! Please fill out the form below.")

# Form for structured data entry
with st.form(key="user_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    age = st.number_input("Age", min_value=1)
    message = st.text_area("Message")

    submit_button = st.form_submit_button("Submit")

if submit_button:
    # Send data to API
    payload = {
        "name": name,
        "email": email,
        "age": age,
        "message": message
    }
    response = requests.post(API_URL, json=payload)

    # Display the response in chatbot format
    with st.chat_message("user"):
        st.write("Here is my submitted information:")

    with st.chat_message("assistant"):
        st.write("Thanks for submitting! Here’s what you entered:")
        st.write(f"**Name:** {name}")
        st.write(f"**Email:** {email}")
        st.write(f"**Age:** {age}")
        st.write(f"**Message:** {message}")

    # Handle API response
    if response.status_code == 200:
        st.success("Form submitted successfully!")
    else:
        st.error("Error submitting form!")
