import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from google import genai
engine = create_engine(
    'mssql+pyodbc://.\\SQLEXPRESS/SalesIntelligenceDB'
    '?driver=ODBC+Driver+17+for+SQL+Server'
    '&trusted_connection=yes'
    '&TrustServerCertificate=yes'
)

query = """
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
"""

df = pd.read_sql(query, engine)
print("Customers pulled:", len(df))
print(df.head())
print(df.describe())

#  features for clustering 
features = ['total_orders', 'total_spent', 'avg_order_value', 'recency_days', 'categories_purchased']
X = df[features].copy()

# Scaling the data  distance-based
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

#  optimal number of clusters using Elbow Method 
inertia = []
K_range = range(2, 10)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertia.append(km.inertia_)

import matplotlib.pyplot as plt
plt.figure(figsize=(8,5))
plt.plot(K_range, inertia, marker='o')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method For Optimal k')
plt.savefig('elbow_plot.png', dpi=150)
plt.show()
print("Elbow plot saved.")


# clustering with k=5
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
df['segment'] = kmeans.fit_predict(X_scaled)

#  Profile each segment 
segment_profile = df.groupby('segment')[features].mean().round(2)
segment_profile['customer_count'] = df.groupby('segment').size()

print("\nSegment Profiles:")
print(segment_profile)

segment_profile.to_csv('segment_profiles.csv')
print("\nSaved to segment_profiles.csv")

client = genai.Client(api_key="YOUR-API-KEY-HERE")

persona_prompt = f"""
You are a senior marketing data analyst. Below are 5 customer segments from a Pakistani e-commerce platform, 
generated using KMeans clustering on order behavior.

{segment_profile.to_string()}

For each segment, write:
1. A short, memorable persona name (2-4 words)
2. A 2-3 sentence description of who this customer is and their shopping behavior
3. One specific marketing recommendation for this segment

Format your response clearly with headers for each segment (Segment 0, Segment 1, etc).
Keep the tone professional, like a real business analytics report.
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=persona_prompt
)

print(response.text)

# Save personas to a file
with open('customer_personas.md', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("\nPersonas saved to customer_personas.md")
