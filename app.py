# Portfolio Risk Analyzer - Gemini 1.5 Flash (with OpenAI backup)

import streamlit as st
import pandas as pd
import requests
from PIL import Image
import base64
from io import BytesIO
import tempfile
import google.generativeai as genai  # ✅ Gemini SDK

# Optional: import openai  # (OpenAI backup code commented below)

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a **screenshot** of your portfolio and receive an AI-powered table extraction.")

# Simulated login
st.session_state.authenticated = True
st.session_state.username = "debug_user"
username = st.session_state.username
st.sidebar.success(f"Welcome, {username}!")

# Configure Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 🧠 Gemini-powered screenshot parsing
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
You are a financial assistant. Extract the investment table from this screenshot. Output it in valid CSV format with two columns: 'Stock' and 'Amount Invested'. Return only the CSV table and nothing else.
"""
    model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ Updated model name
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

    # Try to parse as CSV
    if "Stock" in text_output and "Amount" in text_output and "," in text_output:
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

# --------------------------------------------------------------------------------
# 🗃️ OpenAI backup code (commented for future use)
# import openai
# openai_api_key = st.secrets["OPENAI_API_KEY"]
# def extract_table_using_gpt(image_file, api_key):
#     # Upload to imgbb and call OpenAI with gpt-4o
#     # Fallback to gpt-3.5-turbo on quota error
#     # Parse output as CSV using pandas

