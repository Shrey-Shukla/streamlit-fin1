# Portfolio Risk Analyzer - Streamlit + GPT Vision (Screenshot Only)

import streamlit as st
import pandas as pd
import requests
from PIL import Image
import base64
from io import BytesIO
import openai
import tempfile

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a **screenshot** of your portfolio (with columns like `Stock`, `Amount Invested`) to receive an AI-powered risk summary.")

# 🔓 Temporary bypass of login
st.session_state.authenticated = True
st.session_state.username = "debug_user"

username = st.session_state.username
st.sidebar.success(f"Welcome, {username}!")
openai_api_key = st.secrets["OPENAI_API_KEY"]

# 🔍 GPT Vision + fallback function
def extract_table_using_gpt(image_file, api_key):
    imgbb_key = "e13ed12a576ec71e5c53cb86220eb9e8"

    # Upload image
    st.info("Uploading image to ImgBB and sending to GPT...")
    img = Image.open(image_file).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    try:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": imgbb_key, "image": img_str}
        )
        image_url = response.json()["data"]["url"]
    except Exception as e:
        st.error(f"ImgBB upload failed: {e}")
        return pd.DataFrame()

    messages = [
        {
            "role": "system",
            "content": "You are an expert in extracting investment tables from screenshots."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract a table with columns 'Stock' and 'Amount Invested'. Return it in CSV format."
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
        with st.spinner("Using GPT-4o..."):
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            model_used = "gpt-4o"
    except openai.APIError:
        try:
            with st.spinner("Falling back to GPT-3.5..."):
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                model_used = "gpt-3.5-turbo"
        except Exception as fallback_error:
            st.error(f"GPT-3.5 fallback also failed: {fallback_error}")
            return pd.DataFrame()

    text_output = response.choices[0].message.content.strip()
    st.success(f"Extracted table using **{model_used}**")
    st.code(text_output)

    # Try parsing
    if "Stock" in text_output and "Amount" in text_output and "," in text_output:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8") as temp_file:
                temp_file.write(text_output)
                temp_file_path = temp_file.name
            df = pd.read_csv(temp_file_path)
            return df
        except Exception as e:
            st.warning(f"Could not parse extracted text into a table: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ GPT output does not contain a valid table structure.")
        return pd.DataFrame()


# 🖼️ Upload Section (Screenshot Only)
st.subheader("📸 Upload Screenshot")
upload_type = st.radio("Upload format", ["Screenshot Image"], index=0)
uploaded_file = st.file_uploader("Upload your portfolio screenshot", type=["png", "jpg", "jpeg"], key="main_upload")

df = pd.DataFrame()
if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gpt(uploaded_file, openai_api_key)

if not df.empty:
    st.subheader("✅ Processed Portfolio Table")
    st.dataframe(df)
