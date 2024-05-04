import streamlit as st
from agents.planner_agent import generate_response as gen_resp_planner
from agents.executer_agent import run
import os
import shutil


SAVED_SESSIONS = [
    "Generate a stock price analysis report in markdown report to compare the stock prices of AAPL and MSFT for the last 10 days including visual charts and your financial price analysis comments.",
    "What is the TSLA stock price for the last 10 days?"
]

def delete_images():
    folder = 'images'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

st.title("🦜💰 Groq Stock Price Analysis Custom Agents")

if "plannermessages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["plannermessages"] = []

for msg in st.session_state.plannermessages:
    with st.chat_message(msg["role"]):
        # check msg["content"] is not None or Empty String
        if msg["content"]:
            st.write(msg["content"])

# First, try to get the user_prompt from the chat_input
user_prompt = st.chat_input()

# If the chat_input is empty, try to get the user_prompt from the selectbox
if not user_prompt:
    user_prompt = st.selectbox(
        "Choose a sample question or ask your own question?",
        sorted(SAVED_SESSIONS),
        index=None,
        placeholder="Select from sample questions...",
    )

# If both are empty, set the user_prompt to None
if not user_prompt:
    user_prompt = None

# Continue with the rest of your code
if user_prompt:
    with st.chat_message("user"):
        st.session_state.plannermessages.append({"role": "user", "content": user_prompt})
        st.write(user_prompt)
    with st.chat_message("assistant"):
        response = gen_resp_planner()
        st.write(response["response"])
        st.session_state.plannermessages.append({"role": "assistant", "content": response['response']})
        while True:
            if response['match_found']:
                response = run(response['report'])
                delete_images()
            else:
                break


#generate_response_executer("I need stock price for NVDA for the last 5 days.")
