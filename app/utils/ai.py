import streamlit as st
from google import genai

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key="YOUR-API-KEY-HERE")

SCHEMA_CONTEXT = """
You are a SQL expert working with a Microsoft SQL Server database called SalesIntelligenceDB.

Tables:
customers (customer_id BIGINT, customer_since DATE)
products (sku NVARCHAR, category NVARCHAR)
payments (payment_id INT, payment_method NVARCHAR)
dates (date_id DATE, year INT, month INT, quarter INT, day_of_week NVARCHAR, month_year NVARCHAR, fiscal_year NVARCHAR)
sales (item_id BIGINT, increment_id BIGINT, customer_id BIGINT, sku NVARCHAR, payment_method NVARCHAR,
       order_date DATE, status NVARCHAR, status_grouped NVARCHAR, price DECIMAL, qty_ordered INT,
       grand_total DECIMAL, discount_amount DECIMAL, discount_pct DECIMAL, revenue_per_unit DECIMAL,
       is_return BIT, bi_status NVARCHAR)

Relationships:
sales.customer_id -> customers.customer_id
sales.sku -> products.sku
sales.payment_method -> payments.payment_method
sales.order_date -> dates.date_id

status_grouped values: completed, cancelled, refunded, pending, on_hold, fraud

Note: each row in sales is one line item. An "order" means a unique increment_id —
use COUNT(DISTINCT increment_id) when asked about orders. "Line items" means raw row count.

Write only a single valid T-SQL SELECT query to answer the user's question.
No explanation, no markdown, no backticks. Only the raw SQL query.
Never write INSERT, UPDATE, DELETE, DROP, or ALTER statements.
"""

FORBIDDEN_WORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'EXEC']

import streamlit as st

@st.cache_data(ttl=3600)
def generate_personas(_client, segment_profile_str: str) -> str:
    persona_prompt = f"""
You are a senior marketing data analyst. Below are 5 customer segments from a Pakistani e-commerce platform,
generated using KMeans clustering on order behavior.

{segment_profile_str}

For each segment, write:
1. A short, memorable persona name (2-4 words)
2. A 2-3 sentence description of who this customer is and their shopping behavior
3. One specific marketing recommendation for this segment

Format your response in markdown with a level-3 header for each segment (### Segment 0, ### Segment 1, etc).
Keep the tone professional, like a real business analytics report.
"""
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=persona_prompt
    )
    return response.text