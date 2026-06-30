import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import get_dashboard_data

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
st.title("Executive dashboard")

with st.spinner("Loading dashboard data..."):
    data = get_dashboard_data()

kpis = data["kpis"]

#  KPI Cards 
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total revenue", f"PKR {kpis['total_revenue']/1e9:.2f}bn")
col2.metric("Total orders", f"{int(kpis['total_orders']):,}")
col3.metric("Avg order value", f"PKR {kpis['avg_order_value']:,.0f}")
col4.metric("Cancellation rate", f"{kpis['cancellation_rate']:.1f}%")

st.divider()

#  Monthly Revenue Trend 
st.subheader("Monthly revenue trend")
monthly = data["monthly_revenue"].copy()
monthly["date_id"] = pd.to_datetime(monthly["date_id"])
fig_trend = px.line(
    monthly, x="date_id", y="revenue",
    labels={"date_id": "Month", "revenue": "Revenue (PKR)"}
)
fig_trend.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Order status breakdown")
    status_df = data["status_breakdown"]
    fig_status = px.pie(
        status_df, names="status_grouped", values="total_orders",
        hole=0.5
    )
    fig_status.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("Revenue by category")
    cat_df = data["category_revenue"]
    fig_cat = px.bar(
        cat_df, x="revenue", y="category", orientation="h",
        labels={"revenue": "Revenue (PKR)", "category": ""}
    )
    fig_cat.update_layout(template="plotly_dark", height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Cancellation rate by category")
    cancel_df = data["category_cancellation"]
    fig_cancel = px.bar(
        cancel_df, x="cancellation_rate", y="category", orientation="h",
        labels={"cancellation_rate": "Cancellation rate (%)", "category": ""}
    )
    fig_cancel.update_layout(template="plotly_dark", height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_cancel, use_container_width=True)

with col_right2:
    st.subheader("Revenue by payment method")
    pay_df = data["payment_methods"]
    fig_pay = px.bar(
        pay_df, x="revenue", y="payment_method", orientation="h",
        labels={"revenue": "Revenue (PKR)", "payment_method": ""}
    )
    fig_pay.update_layout(template="plotly_dark", height=400, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_pay, use_container_width=True)