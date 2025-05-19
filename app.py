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

# Simple login using Streamlit session_state (DISABLED FOR DEBUGGING)
st.session_state.authenticated = True
st.session_state.username = "debug_user"

# After login
username = st.session_state.username
st.sidebar.success(f"Welcome, {username}!")
openai_api_key = st.secrets["OPENAI_API_KEY"]




# Only show Screenshot mode
upload_type = st.radio("Select upload format", ["Screenshot Image"], index=0)
uploaded_file = st.file_uploader("Upload your Portfolio", type=["png", "jpg", "jpeg"], key="main_upload")

if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gpt(uploaded_file, openai_api_key)
if 'df' in locals() and not df.empty:
        st.subheader("✅ Processed Portfolio Table")
        st.dataframe(df)


def extract_table_using_gpt(image_file, api_key):
    img = Image.open(image_file).convert("RGB")
    st.image(img, caption="Uploaded Screenshot", use_column_width=True)

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
    except Exception as e:
        st.error(f"Invalid response from ImgBB: {e}")
        return pd.DataFrame()

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

    openai_client = openai.OpenAI(api_key=api_key)
    try:
        with st.spinner("Calling GPT-4o..."):
            model_used = "gpt-4o"
            response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 429:
            st.warning("gpt-4o quota exceeded. Falling back to gpt-3.5-turbo.")
            with st.spinner("Calling GPT-3.5-turbo..."):
                model_used = "gpt-3.5-turbo"
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                    )
                except Exception as fallback_error:
                    st.error(f"OpenAI fallback call also failed: {fallback_error}")
                    return pd.DataFrame()
        else:
            st.error(f"OpenAI API call failed: {e}")
            return pd.DataFrame()

    text_output = response.choices[0].message.content.strip()
    st.subheader("📋 Extracted Table (raw)")
    st.code(text_output, language="csv")
    st.info(f"✅ Response generated using: {model_used}")

    try:
        if "Stock" in text_output and "Amount" in text_output and "," in text_output:
            df = pd.read_csv(pd.compat.StringIO(text_output))
        else:
            st.warning("⚠️ GPT output does not appear to be a clean CSV with 'Stock' and 'Amount Invested'. Showing raw output only.")
            df = pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to parse GPT output into table: {e}")
        df = pd.DataFrame()

    return df


