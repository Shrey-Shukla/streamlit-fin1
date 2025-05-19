import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO, StringIO
import tempfile
import google.generativeai as genai
from fpdf import FPDF

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a screenshot of your portfolio. The system intelligently extracts investments and amounts from even messy layouts.")

# ✅ Ensure API key is present
if "GEMINI_API_KEY" not in st.secrets or not st.secrets["GEMINI_API_KEY"]:
    st.error("🚫 Gemini API key not found. Please set GEMINI_API_KEY in .streamlit/secrets.toml.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
st.session_state.authenticated = True
st.session_state.username = "debug_user"
st.sidebar.success(f"Welcome, {st.session_state.username}!")

# 📄 PDF Report Generator
def generate_pdf(df, recommendation, ai_summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Portfolio Risk Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Invested: ₹{df['Amount'].sum():,.0f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Extracted Portfolio Table", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(0, 10, f"{row['Investment']}: ₹{row['Amount']:,.0f}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Final Recommendation", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 10, recommendation)

    if ai_summary:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "AI-Generated Summary", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 10, ai_summary)

    output = BytesIO()
    pdf.output(output)
    return output.getvalue()

# 🧠 Flexible parser for noisy CSV
def parse_flexible_csv(text_output):
    rows = []
    for line in text_output.strip().splitlines():
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) == 2:
            rows.append(parts)

    if len(rows) < 2:
        return pd.DataFrame()

    headers = [col.lower() for col in rows[0]]
    name_col = 0
    amount_col = 1

    if "amount" not in headers[1] and "invest" not in headers[1]:
        name_col = 1
        amount_col = 0

    data = []
    for r in rows[1:]:
        try:
            name = r[name_col]
            amt = float(r[amount_col].replace("₹", "").replace(",", ""))
            data.append([name, amt])
        except:
            continue

    df = pd.DataFrame(data, columns=["Investment", "Amount"])
    return df

# 🧠 Gemini Table Extraction with 400-proofing
def extract_table_using_gemini(image_file):
    with st.spinner("🔍 Analyzing screenshot with Gemini..."):
        prompt = """
You're a financial assistant. Analyze the screenshot and extract a clean list of investments.

For each row, extract:
1. The investment name (fund, stock, or plan)
2. The invested amount (in INR)

Even if headers are inconsistent, infer from context. Output a CSV with headers: Investment, Amount. Return only the CSV.
"""
        try:
            img = Image.open(image_file).convert("RGB")
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([prompt, img], stream=False)
            text_output = response.text.strip()
        except Exception as e:
            st.error(f"🚫 Gemini Vision API call failed: {e}")
            return pd.DataFrame()

    st.success("✅ Gemini response received")
    st.code(text_output)
    return parse_flexible_csv(text_output)

# 📤 Upload Interface
st.subheader("📸 Upload Screenshot")
uploaded_file = st.file_uploader("Upload your portfolio screenshot", type=["png", "jpg", "jpeg"], key="main_upload")

df = pd.DataFrame()
if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gemini(uploaded_file)

# ✅ Show Table + Risk + Download
if not df.empty:
    st.subheader("✅ Extracted Portfolio Table")
    st.dataframe(df)

    st.subheader("📉 Portfolio Risk Summary")

    try:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df = df.dropna(subset=["Amount"])
        total_invested = df["Amount"].sum()
        st.write(f"**Total Invested:** ₹{total_invested:,.0f}")

        df["Allocation %"] = df["Amount"] / total_invested * 100
        high_risk = df[df["Allocation %"] > 30]

        if not high_risk.empty:
            st.warning("⚠️ High concentration in:")
            st.dataframe(high_risk[["Investment", "Amount", "Allocation %"]])
            recommendation = "Diversify your portfolio by reducing high exposure stocks and reviewing smaller allocations."
        else:
            st.success("✅ Diversified: no holding exceeds 30% allocation.")
            recommendation = "Your portfolio looks balanced. Continue monitoring allocation periodically."

        st.subheader("🧠 AI-Generated Summary")
        summary_prompt = f"Write a one-paragraph risk analysis for this portfolio:\n{df.to_csv(index=False)}"
        ai_summary = genai.GenerativeModel("gemini-1.5-flash").generate_content([summary_prompt]).text.strip()
        st.markdown(ai_summary)

        st.subheader("📌 Final Recommendation")
        st.success(recommendation)

        st.subheader("📤 Download")
        st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), "portfolio.csv", "text/csv")
        st.download_button("⬇️ Download PDF Report", generate_pdf(df, recommendation, ai_summary), "portfolio_summary.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Risk analysis failed: {e}")
