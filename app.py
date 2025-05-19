# Portfolio Risk Analyzer - Gemini Version (with OpenAI backup)

import streamlit as st
import pandas as pd
import requests
from PIL import Image
import base64
from io import BytesIO
import tempfile
import google.generativeai as genai  # ✅ Gemini SDK

# Optional: import openai  # Used only in backup (commented)

# App config
st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a **screenshot** of your portfolio and receive an AI-powered table extraction.")

# Simulated login
st.session_state.authenticated = True
st.session_state.username = "debug_user"
username = st.session_state.username
st.sidebar.success(f"Welcome, {username}!")

# 🔐 Read Gemini key from secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 🔍 GPT alternative: Gemini-based screenshot extraction
def extract_table_using_gemini(image_file):
    imgbb_key = "e13ed12a576ec71e5c53cb86220eb9e8"

    st.info("Uploading image to ImgBB and sending to Gemini...")
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

    prompt = """
You are a financial assistant. Extract the investment table from the image. Output only a clean CSV format with columns: 'Stock', 'Amount Invested'.
Do not include any explanation or notes. Only return the CSV-formatted text.
"""
    model = genai.GenerativeModel("gemini-pro-vision")
    try:
        with st.spinner("Processing with Gemini..."):
            response = model.generate_content(
                [prompt, Image.open(image_file)],
                stream=False
            )
            text_output = response.text.strip()
    except Exception as e:
        st.error(f"Gemini API call failed: {e}")
        return pd.DataFrame()

    st.success("✅ Gemini response received")
    st.code(text_output)

    # Try to parse output
    if "Stock" in text_output and "," in text_output:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8") as temp_file:
                temp_file.write(text_output)
                temp_file_path = temp_file.name
            df = pd.read_csv(temp_file_path)
            return df
        except Exception as e:
            st.warning(f"Could not parse Gemini output into a table: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ Gemini output does not contain a valid table structure.")
        return pd.DataFrame()


# 🖼️ Upload interface
st.subheader("📸 Upload Screenshot")
uploaded_file = st.file_uploader("Upload your portfolio screenshot", type=["png", "jpg", "jpeg"], key="main_upload")

# 📥 Process upload
df = pd.DataFrame()
if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gemini(uploaded_file)

# 📊 Display table
if not df.empty:
    st.subheader("✅ Extracted Portfolio Table")
    st.dataframe(df)

