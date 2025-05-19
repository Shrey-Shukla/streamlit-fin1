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
import tempfile

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

upload_type = st.radio("Select upload format", ["CSV File", "Screenshot Image"])
uploaded_file = st.file_uploader("Upload your Portfolio", type=["csv", "png", "jpg", "jpeg"], key="main_upload")

if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio")
    if process_now:
        if upload_type == "CSV File":
            try:
                df = pd.read_csv(uploaded_file, encoding_errors='replace', on_bad_lines='skip')
                st.success("CSV successfully loaded.")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
                df = pd.DataFrame()
        else:
            df = extract_table_using_gpt(uploaded_file, openai_api_key)

        if not df.empty:
            st.subheader("✅ Processed Portfolio Table")
            st.dataframe(df)
# Removed duplicate file_uploader

def extract_table_using_gpt(image_file, api_key):
    img = Image.open(image_file).convert("RGB")
    st.image(img, caption="Uploaded Screenshot", use_column_width=True)

    # Save temporarily and upload to ImgBB
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        img.save(tmp.name, format="PNG")
        tmp_path = tmp.name

    imgbb_key = "e13ed12a576ec71e5c53cb86220eb9e8"
    with open(tmp_path, "rb") as f:
        upload = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": imgbb_key},
            files={"image": f}
        )

    if upload.status_code != 200:
        st.error("Failed to upload image to ImgBB. Please try again.")
        return pd.DataFrame()

    try:
        image_url = upload.json()["data"]["url"]
    except:
        st.error("Invalid response from ImgBB.")
        return pd.DataFrame()

    # Construct GPT-4o vision prompt
    messages = [
        {
            "role": "system",
            "content": "You are an expert in reading screenshots and extracting financial data."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract a table with columns 'Stock' and 'Amount Invested' from the image below."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ]

    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
        )
    except Exception as e:
        st.error(f"OpenAI API call failed: {e}")
        return pd.DataFrame()

    text_output = response["choices"][0]["message"]["content"]
    st.subheader("📋 Extracted Table (raw)")
    st.code(text_output, language="csv")

    try:
        df = pd.read_csv(pd.compat.StringIO(text_output)) if "Stock" in text_output else pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to parse GPT output into table: {e}")
        df = pd.DataFrame()

    return df
