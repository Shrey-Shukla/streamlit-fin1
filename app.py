# Portfolio Risk Analyzer - MVP using Streamlit + OpenAI + Pandas + Free Login via session_state

import streamlit as st
import pandas as pd
import requests
import datetime
import os
from PIL import Image
import base64
from io import BytesIO
import openai

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")

st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload your portfolio (CSV or Screenshot of a table with `Stock` and `Amount Invested`) and get an AI-powered risk summary.")

# Simple login using Streamlit session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.sidebar:
        st.subheader("🔐 Login")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if username_input == "demo" and password_input == "demo197":
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# After login
username = st.session_state.username
st.sidebar.success(f"Welcome, {username}!")
openai_api_key = st.secrets["OPENAI_API_KEY"]
