import streamlit as st
import pandas as pd
from vanna.remote import VannaDefault

# ---------------------------------------------------------------------------
# Vanna + Streamlit Example App
# ---------------------------------------------------------------------------
# Setup: 
# 1. pip install vanna streamlit pandas
# 2. Run with: streamlit run streamlit_chat_app.py
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide")
st.title("Vanna AI - SQL Generator App")
st.write("This is a simple example of how to build a chat interface for your database using Vanna and Streamlit.")

# Sidebar for Configuration
st.sidebar.title("API Configuration")
st.sidebar.markdown(
    "To get your API key, sign up at [vanna.ai](https://vanna.ai/)."
)

api_key = st.sidebar.text_input("Vanna API Key", type="password")
vanna_model = st.sidebar.text_input("Vanna Model Name", value="chinook")

# Initialize Vanna based on session state
if "vn" not in st.session_state and api_key and vanna_model:
    try:
        vn = VannaDefault(api_key=api_key, vanna_model=vanna_model)
        
        # Connect to a sample database (using sqlite sample for this example)
        vn.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')
        st.session_state["vn"] = vn
        st.sidebar.success("Successfully connected to Vanna!")
    except Exception as e:
        st.sidebar.error(f"Failed to connect: {e}")

# Chat Interface
if "vn" in st.session_state:
    vn = st.session_state["vn"]

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["type"] == "text":
                st.markdown(message["content"])
            elif message["type"] == "code":
                st.code(message["content"], language="sql")
            elif message["type"] == "dataframe":
                st.dataframe(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask a question about your data (e.g. 'What are the top 5 artists by sales?')"):
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response using Vanna
        with st.chat_message("assistant"):
            with st.spinner("Generating SQL and running query..."):
                try:
                    # 1. Generate SQL
                    sql = vn.generate_sql(question=prompt)
                    st.session_state.messages.append({"role": "assistant", "type": "code", "content": sql})
                    st.code(sql, language="sql")
                    
                    # 2. Run SQL to get Dataframe (if generation was successful)
                    if sql:
                        df = vn.run_sql(sql=sql)
                        if isinstance(df, pd.DataFrame):
                             st.session_state.messages.append({"role": "assistant", "type": "dataframe", "content": df})
                             st.dataframe(df)
                        else:
                             msg = "Query executed but no data was returned."
                             st.session_state.messages.append({"role": "assistant", "type": "text", "content": msg})
                             st.warning(msg)
                             
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": error_msg})
                    st.error(error_msg)
else:
    st.info("Please enter your Vanna API Key and Model Name in the sidebar to start.")
