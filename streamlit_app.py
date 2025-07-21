import streamlit as st
import pandas as pd

st.set_page_config("Campaign Budget Allocator", layout="wide")
st.title("📊 Campaign Budget Allocation Advisor")

uploaded_file = st.file_uploader("Upload your campaign performance CSV (e.g. from Google Ads)", type=["csv"])

if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file, skiprows=2)
        df = df_raw[~df_raw['Campaign'].str.contains("Total", na=False)].copy()

        clean_columns = ['Conversions', 'Cost / conv.', 'CTR', 'Clicks', 'Conv. rate', 'Budget']

        for col in clean_columns:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace('--', '', regex=False)
                    .str.replace('%', '', regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=['Conversions', 'Cost / conv.', 'CTR', 'Budget'], inplace=True)

        avg_row = df_raw[df_raw['Campaign'] == 'Total: Account']
        if avg_row.empty:
            avg_conversions = df['Conversions'].mean()
            avg_cpa = df['Cost / conv.'].mean()
            avg_ctr = df['CTR'].mean()
            avg_conv_rate = df['Conv. rate'].mean() / 100
        else:
            avg_conversions = pd.to_numeric(avg_row['Conversions'], errors='coerce').values[0]
            avg_cpa = pd.to_numeric(avg_row['Cost / conv.'], errors='coerce').values[0]
            avg_ctr = pd.to_numeric(avg_row['CTR'].astype(str).str.replace('%', ''), errors='coerce').values[0]
            avg_conv_rate = pd.to_numeric(avg_row['Conv. rate'].astype(str).str.replace('%', ''), errors='coerce').values[0] / 100

        def get_recommendation(row):
            conv = row['Conversions']
            cpa = row['Cost / conv.']
            ctr = row['CTR']
            clicks = row.get('Clicks', 0) or 0
            budget = row['Budget']

            if conv < avg_conversions and cpa > avg_cpa and ctr < avg_ctr:
                action = "🔻 Decrease Budget"
                reason = "Underperforming on all key metrics"
                new_budget = round(budget * 0.8, 2)
            elif abs(conv - avg_conversions) / avg_conversions <= 0.05:
                if cpa > avg_cpa and ctr < avg_ctr:
                    action = "🔻 Decrease Budget"
                    reason = "Avg conversions, high cost, low CTR"
                    new_budget = round(budget * 0.8, 2)
                elif cpa > avg_cpa and ctr > avg_ctr:
                    action = "🔺 Slight Increase"
                    reason = "Avg conversions, good CTR may drive gains"
                    new_budget = round(budget * 1.1, 2)
                else:
                    action = "🔻 Decrease Budget"
                    reason = "Near-average performance with inefficiencies"
                    new_budget = round(budget * 0.8, 2)
            elif conv > avg_conversions and cpa < avg_cpa and ctr > avg_ctr:
                action = "🔺 Increase Budget"
                reason = "High conversions, low cost, high CTR"
                new_budget = round(budget * 1.2, 2)
            else:
                action = "🔻 Decrease Budget"
                reason = "Performance not clearly above average"
                new_budget = round(budget * 0.8, 2)

            return pd.Series({
                "Budget Action": action,
                "Reason": reason,
                "Suggested Budget": new_budget
            })

        df[['Budget Action', 'Reason', 'Suggested Budget']] = df.apply(get_recommendation, axis=1)

        display_cols = [
            'Campaign', 'Budget', 'Suggested Budget', 'Conversions',
            'Cost / conv.', 'CTR', 'Clicks', 'Budget Action', 'Reason'
        ]

        st.subheader("📋 Budget Recommendations")
        st.dataframe(df[display_cols].sort_values('Budget Action', ascending=False).reset_index(drop=True), use_container_width=True)

        st.download_button(_
