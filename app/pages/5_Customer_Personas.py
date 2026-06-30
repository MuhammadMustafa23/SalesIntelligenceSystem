import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import get_customer_segments, get_segment_profiles
from utils.ai import get_gemini_client, generate_personas

st.set_page_config(page_title="Customer Personas", page_icon="🧩", layout="wide")
st.title("Customer personas")
st.caption("KMeans clustering on repeat-customer behavior, with AI-generated personas for each segment")

with st.spinner("Running customer segmentation..."):
    df = get_customer_segments()
    profile = get_segment_profiles(df)

st.subheader("Segment overview")
display_profile = profile.copy()
display_profile.columns = ["Avg orders", "Avg total spent", "Avg order value", "Avg recency (days)", "Avg categories", "Customer count"]
st.dataframe(display_profile, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Segment sizes")
    fig_size = px.pie(
        profile.reset_index(), names="segment", values="customer_count",
        hole=0.4
    )
    fig_size.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_size, use_container_width=True)

with col2:
    st.subheader("Spend vs order frequency")
    fig_scatter = px.scatter(
        df, x="total_orders", y="total_spent", color="segment",
        size="avg_order_value", hover_data=["categories_purchased"],
        labels={"total_orders": "Total orders", "total_spent": "Total spent (PKR)"}
    )
    fig_scatter.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

st.subheader("AI-generated personas")
with st.spinner("Generating personas with Gemini..."):
    client = get_gemini_client()
    personas_text = generate_personas(client, profile.to_string())

st.markdown(personas_text)