# 📊 Display extracted table + summary
if not df.empty:
    st.subheader("✅ Extracted Portfolio Table")
    st.dataframe(df)

    st.subheader("📉 Portfolio Risk Summary")

    # Clean up column names in case of formatting issues
    df.columns = [col.strip() for col in df.columns]

    try:
        # Ensure numeric values
        df["Amount Invested"] = pd.to_numeric(df["Amount Invested"], errors="coerce")
        df = df.dropna(subset=["Amount Invested"])

        total_invested = df["Amount Invested"].sum()
        st.write(f"**Total Invested:** ₹{total_invested:,.0f}")

        # Concentration risk: any stock >30% of total
        df["Allocation %"] = df["Amount Invested"] / total_invested * 100
        high_risk = df[df["Allocation %"] > 30]

        if not high_risk.empty:
            st.warning("⚠️ Your portfolio is highly concentrated in the following stocks:")
            st.dataframe(high_risk[["Stock", "Amount Invested", "Allocation %"]])
        else:
            st.success("✅ Your portfolio is reasonably diversified (no single stock >30%).")

        # Recommendations
        st.subheader("🧠 AI Recommendations:")
        st.markdown("- Consider rebalancing any stock that exceeds 30% of your total investment.")
        st.markdown("- Diversify across sectors or asset types if all stocks are from the same sector.")
        st.markdown("- Review each stock's fundamentals to align with your risk profile and time horizon.")

    except Exception as e:
        st.error(f"Error during risk analysis: {e}")
