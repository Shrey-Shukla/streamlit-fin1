import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO, StringIO
import tempfile
import google.generativeai as genai
from fpdf import FPDF

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")
st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload a screenshot of your portfolio to extract investment details and get a risk summary.")

st.session_state.authenticated = True
st.session_state.username = "debug_user"
st.sidebar.success(f"Welcome, {st.session_state.username}!")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 📄 Generate downloadable PDF
def generate_pdf(df, recommendation, ai_summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Portfolio Risk Summary", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Invested: ₹{df['Amount Invested'].sum():,.0f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Extracted Portfolio Table", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(0, 10, f"{row['Stock']}: ₹{row['Amount Invested']:,.0f}", ln=True)

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

# 🧹 Clean Gemini CSV output
def clean_gemini_csv(text_output):
    lines = text_output.strip().splitlines()
    lines = [line for line in lines if not line.strip().startswith("|---")]
    lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    if "|" in lines[0]:
        lines = [line.replace("|", ",").strip() for line in lines]
    return "\n".join(lines)

# 🧠 Gemini table extraction
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

    try:
        cleaned = clean_gemini_csv(text_output)
        df = pd.read_csv(StringIO(cleaned))
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not parse Gemini table: {e}")
        return pd.DataFrame()

# 📤 Upload interface
st.subheader("📸 Upload Screenshot")
uploaded_file = st.file_uploader("Upload your portfolio screenshot", type=["png", "jpg", "jpeg"], key="main_upload")

df = pd.DataFrame()
if uploaded_file is not None:
    process_now = st.button("📥 Process Uploaded Portfolio", key="process_button")
    if process_now:
        df = extract_table_using_gemini(uploaded_file)

# 📊 Summary + Export
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

        # 🧠 AI-generated portfolio summary
        st.subheader("🧠 AI-Generated Summary")
        summary_prompt = f"Provide a one-paragraph portfolio analysis for the following table:\n{df.to_csv(index=False)}"
        ai_response = genai.GenerativeModel("gemini-1.5-flash").generate_content(summary_prompt)
        ai_summary = ai_response.text.strip()
        st.markdown(ai_summary)

        st.subheader("📌 Final Recommendation")
        st.success(recommendation)

        # 📥 Downloads
        st.subheader("📤 Download")
        st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), "portfolio.csv", "text/csv")
        st.download_button("⬇️ Download PDF Report", generate_pdf(df, recommendation, ai_summary), "portfolio_summary.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Risk analysis failed: {e}")
