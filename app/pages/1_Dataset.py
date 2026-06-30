import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import run_query, get_raw_csv_stats, get_db_stats

st.set_page_config(page_title="Dataset", page_icon="🗂️", layout="wide")
st.title("Dataset overview")

raw_stats = get_raw_csv_stats("./data/Pakistan Largest Ecommerce Dataset.csv")
db_stats = get_db_stats()

tab1, tab2, tab3 = st.tabs(["Raw data", "Cleaning summary", "Cleaned data"])

with tab1:
    st.subheader("Raw dataset sample")
    st.caption(f"Original Pakistan Largest E-commerce Dataset — {raw_stats['total_rows']:,} rows, {raw_stats['total_columns']} columns")
    raw_sample = pd.read_csv(
        "./data/Pakistan Largest Ecommerce Dataset.csv",
        nrows=20,
        low_memory=False
    )
    st.dataframe(raw_sample, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total rows", f"{raw_stats['total_rows']:,}")
    col2.metric("Total columns", raw_stats['total_columns'])
    col3.metric("Fully empty rows", f"{raw_stats['fully_empty_rows']:,}")

with tab2:
    st.subheader("What was cleaned")
    st.markdown("""
| Issue | Action taken |
|---|---|
| 5 fully empty columns (`Unnamed: 21-25`) | Dropped |
| ~464K fully empty rows | Dropped |
| 17 inconsistent order statuses | Normalized into 6 groups (completed, cancelled, refunded, pending, on_hold, fraud) |
| Mixed data types in date/numeric columns | Cast to proper types |
| Negative grand totals (returns) | Flagged with `is_return`, excluded from revenue sums |
| Duplicate SKUs with case/whitespace differences | Normalized to lowercase, deduplicated |
| Duplicate `item_id` values | Removed, kept first occurrence |
    """)

    reduction_pct = round((1 - db_stats['sales'] / raw_stats['total_rows']) * 100, 1)
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows before", f"{raw_stats['total_rows']:,}")
    col2.metric("Rows after", f"{db_stats['sales']:,}")
    col3.metric("Reduction", f"{reduction_pct}%")

with tab3:
    st.subheader("Cleaned data (live from SQL Server)")
    df = run_query("""
        SELECT TOP 50 item_id, customer_id, sku, payment_method, order_date,
               status_grouped, price, qty_ordered, grand_total
        FROM sales
        ORDER BY order_date DESC
    """)
    st.dataframe(df, use_container_width=True)
    st.caption("Showing latest 50 transactions from the `sales` table")