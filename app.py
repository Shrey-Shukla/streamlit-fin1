import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import tempfile
import google.generativeai as genai

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a **screenshot** of your portfolio to extract investment details and get a risk summary.")

st.session_state.authenticated = True
st.session_state.username = "debug_user"
st.sidebar.success(f"Welcome, {st.session_state.username}!")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def extract_table_using_gemini(image_file):
    with st.spinner("🔍 Processing screenshot with Gemini..."):
        prompt = """
You are a financial assistant. Extract the investment table from this screenshot.
Output only a valid CSV table with two columns: 'Stock' and 'Amount Invested'.
No explanation or commentary — only the raw table.
"""
        try:
            img = Image.open(image_file).convert("RGB")
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, img], stream=False)
            text_output = response.text.strip()
        except Exception as e:
            st.error(f"Gemini Vision failed: {e}")
            return pd.DataFrame()

    st.success("✅ Gemini response received")
    st.code(text_output)

    if "Stock" in text_output and "Amount" in text_output and "," in text_output:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8") as temp_file:
                temp_file.write(text_output)
                temp_file_path = temp_file.name
            df = pd.read_csv(temp_file_path)
            return df
        except Exception as e:
            st.warning(f"Failed to parse table: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ Output doesn't contain a valid table.")
        return pd.DataFrame()

# Upload interface
st.subheader("📸 Upload Screenshot")
uploaded_file = st.file_uploader("Upload your portfolio screenshot", type=["png", "jpg", "jpeg"], key="main_upload")

df = pd.DataFrame()
if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gemini(uploaded_file)

# Display + Risk Summary + Final Recommendation
if not df.empty:
    st.subheader("✅ Extracted Portfolio Table")
    st.dataframe(df)

    st.subheader("📉 Portfolio Risk Summary")
    df.columns = [col.strip() for col in df.columns]

    try:
        df["Amount Invested"] = pd.to_numeric(df["Amount Invested"], errors="coerce")
        df = df.dropna(subset=["Amount Invested"])
        total_invested = df["Amount Invested"].sum()
        st.write(f"**Total Invested:** ₹{total_invested:,.0f}")

        df["Allocation %"] = df["Amount Invested"] / total_invested * 100
        high_risk = df[df["Allocation %"] > 30]

        if not high_risk.empty:
            st.warning("⚠️ High concentration in:")
            st.dataframe(high_risk[["Stock", "Amount Invested", "Allocation %"]])
            recommendation = "Diversify your portfolio by reducing high exposure stocks and reviewing smaller allocations."
        else:
            st.success("✅ Diversified: no stock exceeds 30% allocation.")
            recommendation = "Your portfolio looks balanced. Continue monitoring allocation periodically."

        st.subheader("🧠 AI Recommendations")
        st.markdown("- Rebalance if any holding >30%.")
        st.markdown("- Add more sectors if all holdings are similar.")
        st.markdown("- Align with long-term risk-return goals.")

        # ✅ Final recommendation box
        st.subheader("📌 Final Recommendation")
        st.success(recommendation)

    except Exception as e:
        st.error(f"Risk analysis failed: {e}")
