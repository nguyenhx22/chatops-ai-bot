import streamlit as st
from datetime import datetime

# Initialize session state to store conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to generate chatbot response
def generate_response(user_input):
    if user_input.lower() in ['hello', 'hi', 'hey']:
        return 'Hello! How can I assist you today?'
    elif user_input.lower() in ['how are you', 'how are you doing']:
        return 'I\'m doing great, thanks for asking! How about you?'
    elif user_input.lower() in ['what is your name', 'what\'s your name']:
        return 'I\'m an AI chatbot, and I don\'t have a personal name. I\'m here to help answer your questions and provide information.'
    else:
        return 'I didn\'t quite understand that. Could you please rephrase or ask a different question?'

# Main chatbot app
def main():
    st.title('Streamlit Chatbot App')
    st.write('Welcome to our chatbot app! Type a message below to get started.')

    user_input = st.text_input('You: ', placeholder='Type your message here...')

    if st.button('Send'):
        st.session_state.conversation_history.append(('You', user_input))
        response = generate_response(user_input)
        st.session_state.conversation_history.append(('Chatbot', response))

    # Display conversation history
    st.write('Conversation History:')
    for speaker, message in st.session_state.conversation_history:
        st.write(f'{speaker}: {message}')

if __name__ == '__main__':
    main()