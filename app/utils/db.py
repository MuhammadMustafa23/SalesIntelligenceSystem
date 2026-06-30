import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

@st.cache_resource
def get_engine():
    return create_engine(
        'mssql+pyodbc://.\\SQLEXPRESS/SalesIntelligenceDB'
        '?driver=ODBC+Driver+17+for+SQL+Server'
        '&trusted_connection=yes'
        '&TrustServerCertificate=yes'
    )

@st.cache_data(ttl=3600)
def run_query(query: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(query, engine)

@st.cache_data(ttl=3600)
def get_raw_csv_stats(path: str) -> dict:
    """Reads raw CSV in chunks to get true row/column/null counts without loading 1M rows into memory at once."""
    total_rows = 0
    fully_empty_rows = 0
    n_cols = None
    chunksize = 100_000

    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        if n_cols is None:
            n_cols = chunk.shape[1]
        total_rows += len(chunk)
        fully_empty_rows += chunk.isnull().all(axis=1).sum()

    return {
        "total_rows": total_rows,
        "total_columns": n_cols,
        "fully_empty_rows": int(fully_empty_rows)
    }

@st.cache_data(ttl=3600)
def get_db_stats() -> dict:
    """Pulls real counts from each table in SQL Server."""
    engine = get_engine()
    stats = {}
    tables = ['sales', 'customers', 'products', 'payments', 'dates']
    for t in tables:
        result = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM {t}", engine)
        stats[t] = int(result['cnt'][0])
    return stats

@st.cache_data(ttl=3600)
def get_dashboard_data() -> dict:
    engine = get_engine()

    monthly_revenue = pd.read_sql("""
        SELECT d.date_id, d.year, d.month, SUM(s.grand_total) AS revenue
        FROM sales s
        JOIN dates d ON s.order_date = d.date_id
        WHERE s.status_grouped = 'completed'
        GROUP BY d.date_id, d.year, d.month
        ORDER BY d.date_id
    """, engine)

    status_breakdown = pd.read_sql("""
        SELECT status_grouped, COUNT(*) AS total_orders
        FROM sales
        GROUP BY status_grouped
        ORDER BY total_orders DESC
    """, engine)

    category_revenue = pd.read_sql("""
        SELECT p.category, SUM(s.grand_total) AS revenue
        FROM sales s
        JOIN products p ON s.sku = p.sku
        WHERE s.status_grouped = 'completed'
        GROUP BY p.category
        ORDER BY revenue DESC
    """, engine)

    category_cancellation = pd.read_sql("""
        SELECT p.category,
               COUNT(s.item_id) AS total_orders,
               SUM(CASE WHEN s.status_grouped = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
               ROUND(SUM(CASE WHEN s.status_grouped = 'cancelled' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(s.item_id), 2) AS cancellation_rate
        FROM sales s
        JOIN products p ON s.sku = p.sku
        GROUP BY p.category
        ORDER BY cancellation_rate DESC
    """, engine)

    payment_methods = pd.read_sql("""
        SELECT payment_method, COUNT(*) AS total_orders, SUM(grand_total) AS revenue
        FROM sales
        WHERE status_grouped = 'completed'
        GROUP BY payment_method
        ORDER BY total_orders DESC
    """, engine)

    kpis = pd.read_sql("""
        SELECT
            SUM(CASE WHEN status_grouped = 'completed' THEN grand_total ELSE 0 END) AS total_revenue,
            COUNT(DISTINCT increment_id) AS total_orders,
            AVG(CASE WHEN status_grouped = 'completed' THEN grand_total END) AS avg_order_value,
            SUM(CASE WHEN status_grouped = 'cancelled' THEN 1.0 ELSE 0 END) * 100.0 / COUNT(*) AS cancellation_rate
        FROM sales
    """, engine)

    return {
        "monthly_revenue": monthly_revenue,
        "status_breakdown": status_breakdown,
        "category_revenue": category_revenue,
        "category_cancellation": category_cancellation,
        "payment_methods": payment_methods,
        "kpis": kpis.iloc[0]
    }

@st.cache_data(ttl=3600)
def get_forecast_data() -> dict:
    engine = get_engine()

    forecast = pd.read_sql("""
        SELECT forecast_date, predicted_revenue, lower_bound, upper_bound, is_actual
        FROM revenue_forecast
        ORDER BY forecast_date
    """, engine)

    future_only = forecast[forecast['is_actual'] == 0].copy()
    next_12mo_revenue = future_only['predicted_revenue'].sum()
    avg_confidence_range = (future_only['upper_bound'] - future_only['lower_bound']).mean()

    return {
        "forecast": forecast,
        "next_12mo_revenue": next_12mo_revenue,
        "avg_confidence_range": avg_confidence_range
    }

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

@st.cache_data(ttl=3600)
def get_customer_segments() -> pd.DataFrame:
    engine = get_engine()

    df = pd.read_sql("""
        SELECT 
            s.customer_id,
            COUNT(DISTINCT s.increment_id) AS total_orders,
            SUM(s.grand_total) AS total_spent,
            AVG(s.grand_total) AS avg_order_value,
            DATEDIFF(DAY, MIN(s.order_date), MAX(s.order_date)) AS customer_lifespan_days,
            DATEDIFF(DAY, MAX(s.order_date), '2018-08-28') AS recency_days,
            COUNT(DISTINCT p.category) AS categories_purchased
        FROM sales s
        JOIN products p ON s.sku = p.sku
        WHERE s.status_grouped = 'completed'
        GROUP BY s.customer_id
        HAVING COUNT(DISTINCT s.increment_id) >= 2
    """, engine)

    features = ['total_orders', 'total_spent', 'avg_order_value', 'recency_days', 'categories_purchased']
    X = df[features].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df['segment'] = kmeans.fit_predict(X_scaled)

    return df

@st.cache_data(ttl=3600)
def get_segment_profiles(df: pd.DataFrame) -> pd.DataFrame:
    features = ['total_orders', 'total_spent', 'avg_order_value', 'recency_days', 'categories_purchased']
    profile = df.groupby('segment')[features].mean().round(2)
    profile['customer_count'] = df.groupby('segment').size()
    return profile