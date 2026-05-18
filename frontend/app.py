import streamlit as st
import requests
import pandas as pd

base_url = "http://127.0.0.1:8000"

st.set_page_config(page_title="Smart AI Business Assistant Platform", layout="wide")

st.title("Smart AI Business Assistant Platform")

if "token" not in st.session_state:
    st.session_state.token = None
if "messages" not in st.session_state:
    st.session_state.messages = []

#chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

#tabs
tab1, tab2, tab3, tab4 = st.tabs(["Assistant", "Memory", "Dashboard", "Login/Register"])

#tab1
with tab1:
    # if not st.session_state.token:
    #     st.warning("Please log in via the Login tab to access the Assistant.")
    # else:
        st.markdown("### Customer Chat Interface")

        #history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        #input
        if prompt := st.chat_input("Ask a question or say 'I want to buy 5 laptops'"):

            #append user msg
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            history_list = st.session_state.messages[:-1]
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history_list[-4:]])

            #call fastapi
            with st.chat_message("assistant"):
                with st.spinner("Agent is thinking..."):
                    # headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    try:
                        response = requests.post(f"{base_url}/chat", json={"message": prompt, "history": history_text})
                        if response.status_code == 200:
                            reply = response.json().get("reply")
                        else:
                            reply = f"Server Error {response.status_code}: {response.text}"
                    except Exception as e:
                        reply = f"Failed to connect to backend: {e}"

                    # st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

#tab2
with tab2:
    # if not st.session_state.token:
    #     st.warning("Please log in to upload documents.")
    # else:
        st.markdown("### Upload Business Documents")
        uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])

        if st.button("Upload to Memory"):
            if uploaded_file is not None:
                with st.spinner("Processing document..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    # headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    try:
                        response = requests.post(f"{base_url}/upload", files=files)
                        if response.status_code == 200:
                            st.success(response.json().get("message", "Upload successful!"))
                        else:
                            st.error(f"Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"Backend connection error: {e}")
            else:
                st.warning("Please select a file first.")

#tab3
with tab3:
    if not st.session_state.token:
        st.warning("Please log in to view the dashboard.")
    else:
        st.markdown("### Lead Capture Dashboard")
        if st.button("Refresh Leads"):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            try:
                # Assuming /leads is protected in main.py. If not, headers won't hurt.
                response = requests.get(f"{base_url}/leads", headers=headers)
                if response.status_code == 200:
                    leads = response.json()
                    if leads:
                        df = pd.DataFrame(leads)
                        st.dataframe(df, width="stretch")
                    else:
                        st.info("No leads captured yet.")
                else:
                    st.error(f"Failed to fetch leads: {response.text}")
            except Exception as e:
                st.error(f"Backend error: {e}")

#tab4
with tab4:
    st.subheader("Staff Authentication")
    if not st.session_state.token:
        action = st.radio("Action", ["Login", "Register"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Submit"):
            if action == "Register":

                res = requests.post(f"{base_url}/register?username={username}&password={password}&role=admin")
                if res.status_code == 200:
                    st.success("Registered successfully! Please switch to Login above and enter your credentials.")
                else:
                    st.error(f"Registration failed: {res.text}")
            else:

                res = requests.post(f"{base_url}/login", data={"username": username, "password": password})
                if res.status_code == 200:
                    st.session_state.token = res.json().get("access_token")
                    st.success("Logged in! Switch to the Assistant tab.")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        st.success("You are currently logged in.")
        if st.button("Logout"):
            st.session_state.token = None
            st.rerun()