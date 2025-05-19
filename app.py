import streamlit as st
import pandas as pd
import requests
from PIL import Image
import base64
from io import BytesIO
import tempfile
import google.generativeai as genai

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a **screenshot** of your portfolio and receive an AI-powered table + risk summary.")

st.session_state.authenticated = True
st.session_state.username = "debug_user"
st.sidebar.success(f"Welcome, {st.session_state.username}!")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def extract_table_using_gemini(image_file):
    imgbb_key = "e13ed12a576ec71e5c53cb86220eb9e8"

    with st.spinner("📤 Uploading & analyzing screenshot..."):
        try:
            img = Image.open(image_file).convert("RGB")
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=60)
            img_str = base64.b64encode(buffered.getvalue()).decode()

            response = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": imgbb_key, "image": img_str}
            )
            image_url = response.json()["data"]["url"]
        except Exception as e:
            st.error(f"ImgBB upload failed: {e}")
            return pd.DataFrame()

        prompt = """
You are a financial assistant. Extract the investment table from this screenshot.
Output only a valid CSV table with two columns: 'Stock' and 'Amount Invested'.
No notes, no commentary — just the raw table.
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            response = model.generate_content([prompt, Image.open(image_file)], stream=False)
            text_output = response.text.strip()
        except Exception as e:
            st.error(f"Gemini API call failed: {e}")
            return pd.DataFrame()

    st.success("✅ Gemini response received")
    st.code(text_output)

    if "Stock" in text_output and "Amount" in text_output and "," in text_output:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding
