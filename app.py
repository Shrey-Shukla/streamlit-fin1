# Portfolio Risk Analyzer - MVP using Streamlit + OpenAI + Pandas + Free Monetization with Firebase Auth

import streamlit as st
import pandas as pd
import requests
import streamlit_authenticator as stauth
import datetime
import os
from PIL import Image
import base64
from io import BytesIO

import openai  # <-- Ensure OpenAI is imported globally

st.set_page_config(page_title="Portfolio Risk Analyzer", layout="wide")

st.title("📊 AI Portfolio Risk Analyzer")
st.markdown("Upload your portfolio (CSV or Screenshot of a table with `Stock` and `Amount Invested`) and get an AI-powered risk summary.")

# Free login system using streamlit-authenticator
names = ["Demo User"]
usernames = ["demo"]
passwords = ["demo123"]

credentials = {
    "usernames": {
        "demo": {
            "name": "Demo User",
            "password": "$2b$12$KIXxC4dxWQzDTSVTBga9uODMeRQU6PDDXMcNeUXO43UBoF5zAwvUm"
        }
    }
}

authenticator = stauth.Authenticate(credentials, "portfolio_app", "abcdef", cookie_expiry_days=1)

name, authentication_status, username = authenticator.login(location="sidebar", fields={"Form name": "Login"})

# Simple usage logging function
def log_user_activity(username, action):
    log_file = "user_activity_log.csv"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[now, username, action]], columns=["Timestamp", "Username", "Action"])
    if os.path.exists(log_file):
        entry.to_csv(log_file, mode='a', header=False, index=False)
    else:
        entry.to_csv(log_file, index=False)

if authentication_status:
    st.sidebar.success(f"Welcome, {name}!")
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

    upload_type = st.radio("Select upload format", ["CSV File", "Screenshot Image"])

    uploaded_file = st.file_uploader("Upload your Portfolio", type=["csv", "png", "jpg", "jpeg"])

    def enrich_sector(stock_name):
        sector_map = {
            "HDFC Bank": "Banking",
            "Infosys": "IT",
            "Reliance": "Energy",
            "Maruti Suzuki": "Auto",
            "ITC": "FMCG",
            "ICICI Bank": "Banking",
            "TCS": "IT",
            "Bajaj Finance": "NBFC",
            "Parag Parikh Flexi Cap": "Mutual Fund",
            "SBI Bluechip Fund": "Mutual Fund"
        }
        return sector_map.get(stock_name, "Unknown")

    def extract_table_using_gpt(image_file, api_key):
        img = Image.open(image_file).convert("RGB")
        st.image(img, caption="Uploaded Screenshot", use_column_width=True)

        buffered_io = BytesIO()
        img.save(buffered_io, format="PNG")
        img_str = base64.b64encode(buffered_io.getvalue()).decode()

        prompt = """
The following image is a screenshot of a portfolio table. Extract a list of rows in the format:
[Stock/Fund Name, Amount Invested]

Output only as a table with columns `Stock` and `Amount Invested`, no extra text.
"""

        messages = [
            {"role": "system", "content": "You are an expert in reading screenshots and extracting financial data."},
            {"role": "user", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}]}
        ]

        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
        )

        text_output = response["choices"][0]["message"]["content"]
        df = pd.read_csv(pd.compat.StringIO(text_output)) if "Stock" in text_output else pd.DataFrame()
        return df

    if uploaded_file is not None and openai_api_key:
        try:
            if upload_type == "CSV File":
                df = pd.read_csv(uploaded_file)
            else:
                df = extract_table_using_gpt(uploaded_file, openai_api_key)

            if df.empty or 'Amount Invested' not in df.columns:
                st.error("Could not extract a valid table from image. Please try again with a clearer screenshot.")
            else:
                if 'Sector' not in df.columns:
                    df['Sector'] = df['Stock'].apply(enrich_sector)

                st.subheader("Uploaded Portfolio")
                st.dataframe(df)

                sector_summary = df.groupby("Sector")["Amount Invested"].sum().reset_index().sort_values(by="Amount Invested", ascending=False)
                st.subheader("Investment by Sector")
                st.bar_chart(sector_summary.set_index("Sector"))

                prompt = f"""
You are a financial analyst. Analyze the following investment portfolio:

{df.to_string(index=False)}

Provide insights on:
- Sector concentration risk
- Diversification across industries
- Any missing critical sectors (like healthcare, IT, infra, etc.)
- Suggestions to improve diversification

Respond in structured bullet points.
"""

                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a finance expert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                analysis = response["choices"][0]["message"]["content"]

                st.subheader("📌 AI-Powered Risk Summary")
                st.markdown(analysis)

                log_user_activity(username, "Generated AI Risk Summary")

        except Exception as e:
            st.error(f"Error processing portfolio: {e}")
    else:
        st.info("Please upload a portfolio and enter your OpenAI API key to begin analysis.")
elif authentication_status is False:
    st.error("Incorrect username or password")
elif authentication_status is None:
    st.warning("Please enter your username and password")
