import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_DIR = '/home/coder/coder/star-tracking'

# Page config
st.set_page_config(
    page_title="GitHub Star Tracking",
    page_icon="⭐",
    layout="wide"
)

# Title
st.title("⭐ GitHub Star Tracking Dashboard")
st.caption("Monthly star metrics for Coder repositories")

# ============================================================================
# STAR DATA SECTION
# ============================================================================

@st.cache_data
def load_star_data():
    csv_files = [f for f in os.listdir(DATA_DIR) if f.startswith('github_stars') and f.endswith('.csv')]
    if not csv_files:
        return None
    csv_file = sorted(csv_files)[-1]
    df = pd.read_csv(os.path.join(DATA_DIR, csv_file))
    return df, csv_file

result = load_star_data()

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

csv_data = df.to_csv(index=False)
st.download_button(
    label="Download Stars CSV",
    data=csv_data,
    file_name=f"github_stars_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# ============================================================================
# DOWNLOADS SECTION
# ============================================================================

st.divider()
st.header("📦 Downloads")

def load_downloads_csv(filename):
    """Load a downloads CSV from DATA_DIR if it exists."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def save_uploaded_csv(uploaded_file, filename):
    """Save an uploaded file to DATA_DIR."""
    path = os.path.join(DATA_DIR, filename)
    content = uploaded_file.getvalue()
    with open(path, 'wb') as f:
        f.write(content)
    return path

def detect_date_column(df):
    """Find the most likely date/time column."""
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['date', 'time', 'month', 'day', 'period']):
            return col
    # Fallback: try first column
    return df.columns[0]

def detect_value_column(df, date_col):
    """Find the most likely numeric value column."""
    for col in df.columns:
        if col == date_col:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            return col
        # Try converting
        try:
            pd.to_numeric(df[col].str.replace(',', ''))
            return col
        except (ValueError, AttributeError):
            continue
    return None

def aggregate_monthly(df, date_col, value_col):
    """Aggregate cumulative daily data to monthly downloads.

    The input data has cumulative totals per day. To get monthly
    downloads, we take the last value in each month and subtract
    the last value of the prior month.
    """
    temp = df.copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce')
    temp = temp.dropna(subset=[date_col])

    if not pd.api.types.is_numeric_dtype(temp[value_col]):
        temp[value_col] = pd.to_numeric(
            temp[value_col].astype(str).str.replace(',', ''), errors='coerce'
        )
    temp = temp.dropna(subset=[value_col])
    temp = temp.sort_values(date_col)

    temp['Month'] = temp[date_col].dt.to_period('M').astype(str)

    # Take the last cumulative value per month.
    month_end = temp.groupby('Month')[value_col].last().reset_index()
    month_end.columns = ['Month', 'Cumulative']
    month_end = month_end.sort_values('Month').reset_index(drop=True)

    # Monthly downloads = difference between consecutive month-end totals.
    month_end['Downloads'] = month_end['Cumulative'].diff()
    # First month: use (last value - first value) within that month as
    # a best-effort estimate since we lack the prior month's end total.
    if len(month_end) > 0:
        first_month = month_end['Month'].iloc[0]
        first_month_data = temp[temp['Month'] == first_month][value_col]
        month_end.loc[month_end.index[0], 'Downloads'] = (
            first_month_data.iloc[-1] - first_month_data.iloc[0]
        )

    month_end['Downloads'] = month_end['Downloads'].astype(int)
    return month_end[['Month', 'Downloads', 'Cumulative']]

def render_downloads_section(label, csv_filename, key_prefix):
    """Render upload + charts for a single download dataset."""
    st.subheader(f"{label}")

    existing_df = load_downloads_csv(csv_filename)

    with st.expander(f"Upload / Update {label} CSV", expanded=(existing_df is None)):
        uploaded = st.file_uploader(
            f"Upload {label} CSV",
            type=['csv'],
            key=f"{key_prefix}_upload",
            help="Upload a CSV with date and download count columns."
        )
        if uploaded is not None:
            save_uploaded_csv(uploaded, csv_filename)
            st.success(f"Saved to {csv_filename}. Refresh the page to see updated data.")
            st.cache_data.clear()
            existing_df = load_downloads_csv(csv_filename)

    if existing_df is None:
        st.info(f"No {label.lower()} data yet. Upload a CSV above.")
        return

    # Detect columns
    date_col = detect_date_column(existing_df)
    value_col = detect_value_column(existing_df, date_col)

    if value_col is None:
        st.warning("Could not detect a numeric downloads column. Showing raw data.")
        st.dataframe(existing_df, use_container_width=True, hide_index=True)
        return

    # Aggregate to monthly
    monthly_dl = aggregate_monthly(existing_df, date_col, value_col)

    if monthly_dl.empty:
        st.warning("No valid data after parsing. Check date and value columns.")
        st.dataframe(existing_df.head(10), use_container_width=True, hide_index=True)
        return

    # Metrics
    current_total = monthly_dl['Cumulative'].iloc[-1]
    latest_month_dl = monthly_dl['Downloads'].iloc[-1]
    prev_month_dl = monthly_dl['Downloads'].iloc[-2] if len(monthly_dl) > 1 else latest_month_dl

    m1, m2, m3 = st.columns(3)
    m1.metric("All-Time Downloads", f"{int(current_total):,}")
    m2.metric(
        "Latest Month",
        f"{int(latest_month_dl):,}",
        delta=f"{int(latest_month_dl - prev_month_dl):+,} vs prior month"
    )
    m3.metric("Months Tracked", len(monthly_dl))

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Monthly Downloads")
        chart_df = monthly_dl[['Month', 'Downloads']].set_index('Month')
        st.bar_chart(chart_df)
    with c2:
        st.caption("Cumulative Downloads")
        chart_df = monthly_dl[['Month', 'Cumulative']].set_index('Month')
        st.line_chart(chart_df)

    # Raw data in expander
    with st.expander("View Raw Data"):
        st.dataframe(existing_df, use_container_width=True, hide_index=True)
        dl_csv = existing_df.to_csv(index=False)
        st.download_button(
            label=f"Download {label} CSV",
            data=dl_csv,
            file_name=f"{key_prefix}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key=f"{key_prefix}_download"
        )

# Render both download sections
col_a, col_b = st.columns(2)

with col_a:
    render_downloads_section("Coder Downloads", "coder_downloads.csv", "coder_dl")

with col_b:
    render_downloads_section("Code-Server Downloads", "code_server_downloads.csv", "cs_dl")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
st.caption("To refresh star data, run: `python3 github_star_history.py`")
