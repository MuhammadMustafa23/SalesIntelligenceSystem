import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import get_forecast_data

st.set_page_config(page_title="Forecast", page_icon="🔮", layout="wide")
st.title("Revenue forecast")
st.caption("12-month projection using Facebook Prophet, trained on 26 months of historical sales data")

with st.spinner("Loading forecast..."):
    data = get_forecast_data()

forecast = data["forecast"].copy()
forecast["forecast_date"] = pd.to_datetime(forecast["forecast_date"])

col1, col2 = st.columns(2)
col1.metric("Predicted revenue (next 12 months)", f"PKR {data['next_12mo_revenue']/1e9:.2f}bn")
col2.metric("Avg forecast confidence range", f"PKR {data['avg_confidence_range']/1e6:.1f}M")

st.divider()

st.subheader("Actual vs forecast revenue")

actual = forecast[forecast["is_actual"] == 1]
future = forecast[forecast["is_actual"] == 0]

fig = go.Figure()

# Confidence band
fig.add_trace(go.Scatter(
    x=pd.concat([future["forecast_date"], future["forecast_date"][::-1]]),
    y=pd.concat([future["upper_bound"], future["lower_bound"][::-1]]),
    fill='toself',
    fillcolor='rgba(99, 110, 250, 0.15)',
    line=dict(color='rgba(255,255,255,0)'),
    name='Confidence interval',
    showlegend=True
))

# Actual line
fig.add_trace(go.Scatter(
    x=actual["forecast_date"], y=actual["predicted_revenue"],
    mode='lines', name='Actual',
    line=dict(color='#00CC96', width=2)
))

# Forecast line
fig.add_trace(go.Scatter(
    x=future["forecast_date"], y=future["predicted_revenue"],
    mode='lines', name='Forecast',
    line=dict(color='#636EFA', width=2, dash='dash')
))

fig.update_layout(
    template="plotly_dark",
    height=500,
    xaxis_title="Date",
    yaxis_title="Revenue (PKR)",
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Monthly forecast details")
display_df = future[future["predicted_revenue"] > 0][
    ["forecast_date", "predicted_revenue", "lower_bound", "upper_bound"]
].copy()
display_df.columns = ["Month", "Predicted revenue", "Lower bound", "Upper bound"]
display_df["Month"] = display_df["Month"].dt.strftime("%B %Y")
for col in ["Predicted revenue", "Lower bound", "Upper bound"]:
    display_df[col] = display_df[col].apply(lambda x: f"PKR {x:,.0f}")

st.dataframe(display_df, use_container_width=True, hide_index=True)