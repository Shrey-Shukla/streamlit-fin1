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

upload_type = st.radio("Select upload format", ["CSV File", "Screenshot Image"])

uploaded_file = st.file_uploader("Upload your Portfolio", type=["csv", "png", "jpg", "jpeg"])

def extract_table_using_gpt(image_file, api_key):
    import tempfile
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
    image_url = upload.json()["data"]["url"]

    # Construct GPT-4o vision prompt
    messages = [
        {"role": "system", "content": "You are an expert in reading screenshots and extracting financial data."},
        {"role": "user", "content": "Extract a table with columns 'Stock' and 'Amount Invested' from the image below."},
        {"role": "user", "content": [
            {
                "type": "image_url",
                "image_url": {"url": image_url}
            }
        ]}
    ]

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
    )

    text_output = response["choices"][0]["message"]["content"]
    try:
        df = pd.read_csv(pd.compat.StringIO(text_output)) if "Stock" in text_output else pd.DataFrame()
    except:
        df = pd.DataFrame()
    return df
