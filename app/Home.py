import streamlit as st
import sys, os
from utils.db import run_query
sys.path.append(os.path.dirname(__file__))
from utils.db import get_db_stats, get_raw_csv_stats

st.set_page_config(
    page_title="Sales Intelligence System",
    page_icon="📊",
    layout="wide"
)

st.title("Sales Intelligence & Forecasting System")
st.caption("End-to-end data analytics project — Pakistan's largest e-commerce dataset (2016–2018)")

st.divider()

with st.spinner("Loading live stats..."):
    raw_stats = get_raw_csv_stats("./data/Pakistan Largest Ecommerce Dataset.csv")
    db_stats = get_db_stats()
    categories=run_query("SELECT COUNT(DISTINCT category) AS cnt from products")['cnt'][0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Raw records", f"{raw_stats['total_rows']:,}")
col2.metric("Cleaned records", f"{db_stats['sales']:,}")
col3.metric("Unique customers", f"{db_stats['customers']:,}")
col4.metric("Product categories", categories)

st.divider()

st.subheader("Project architecture")
st.markdown("""
This project takes a raw, messy e-commerce export and turns it into a full analytics product:

1. **Data cleaning** — Python preprocessing on 1M+ raw transactions, handling nulls, type mismatches, and inconsistent statuses
2. **SQL Server** — normalized star schema (customers, products, payments, dates, sales)
3. **Power BI dashboard** — 4-page report with KPIs, trends, and segmentation visuals
4. **Forecasting** — Prophet time-series model projecting 12 months of revenue
5. **AI layer** — Gemini-powered natural language query tool and KMeans-based customer personas
""")

st.divider()
st.subheader("Explore")
st.markdown("""
Use the sidebar to navigate:
- **Dataset** — see the raw vs. cleaned data
- **Dashboard** — key business metrics and trends
- **Forecast** — 12-month revenue projection
- **Ask Your Data** — type a question, get SQL + an answer
- **Customer Personas** — AI-generated customer segments
""")