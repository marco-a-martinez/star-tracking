import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page config
st.set_page_config(
    page_title="GitHub Star Tracking",
    page_icon="⭐",
    layout="wide"
)

# Title
st.title("⭐ GitHub Star Tracking Dashboard")
st.caption("Monthly star metrics for Coder repositories")

# Load data
@st.cache_data
def load_data():
    csv_files = [f for f in os.listdir('.') if f.startswith('github_stars') and f.endswith('.csv')]
    if not csv_files:
        return None
    # Use most recent file
    csv_file = sorted(csv_files)[-1]
    df = pd.read_csv(csv_file)
    return df, csv_file

result = load_data()

if result is None:
    st.error("No CSV data found. Run `python3 github_star_history.py` first.")
    st.stop()

df, csv_file = result
st.caption(f"Data source: {csv_file}")

# Identify columns
month_col = 'Month'
monthly_cols = [c for c in df.columns if c != month_col and 'All-Time' not in c]
alltime_cols = [c for c in df.columns if 'All-Time' in c]

# Summary metrics
st.subheader("Current Totals")
cols = st.columns(len(alltime_cols))
for i, col in enumerate(alltime_cols):
    repo_name = col.replace(' All-Time', '')
    current_total = df[col].iloc[-1]
    prev_total = df[col].iloc[-2] if len(df) > 1 else current_total
    delta = current_total - prev_total
    cols[i].metric(
        label=repo_name,
        value=f"{current_total:,}",
        delta=f"+{delta:,} this month" if delta > 0 else f"{delta:,} this month"
    )

st.divider()

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly New Stars")
    chart_df = df[[month_col] + monthly_cols].set_index(month_col)
    st.bar_chart(chart_df)

with col2:
    st.subheader("Cumulative Stars Over Time")
    chart_df = df[[month_col] + alltime_cols].set_index(month_col)
    chart_df.columns = [c.replace(' All-Time', '') for c in chart_df.columns]
    st.line_chart(chart_df)

st.divider()

# Data table
st.subheader("Raw Data")
st.dataframe(df, use_container_width=True, hide_index=True)

# Download button
csv_data = df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name=f"github_stars_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# Footer
st.divider()
st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
st.caption("To refresh data, run: `python3 github_star_history.py`")
