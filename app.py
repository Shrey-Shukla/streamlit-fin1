# Portfolio Risk Analyzer - MVP using Streamlit + OpenAI + Pandas + Free Monetization with Firebase Auth

import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
import datetime
import os
from PIL import Image
import base64
from io import BytesIO

import openai  # <-- Ensure OpenAI is imported globally

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")

st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload your portfolio (CSV or Screenshot of a table with `Stock` and `Amount Invested`) and get an AI-powered risk summary.")

# Free login system using streamlit-authenticator
names = ["Demo User"]
usernames = ["demo"]
passwords = ["demo123"]

credentials = {
    "usernames": {
        "demo": {
            "name": "Demo User",
            "password": "$2b$12$KIXxC4dxWQzDTSVTBga9uODMeRQU6PDDXMcNeUXO43UBoF5zAwvUm"
        }
    }
}

authenticator = stauth.Authenticate(credentials, "portfolio_app", "abcdef", cookie_expiry_days=1)

login_result = authenticator.login(location="sidebar", fields={"Form name": "Login"})
if login_result is not None:
    name, authentication_status, username = login_result
else:
    name = authentication_status = username = None
