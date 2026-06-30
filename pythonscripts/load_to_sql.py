import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv('cleaned_ecommerce_data.csv')
df['created_at'] = pd.to_datetime(df['created_at'])
df['Customer Since'] = pd.to_datetime(df['Customer Since'])

engine = create_engine(
    'mssql+pyodbc://.\\SQLEXPRESS/SalesIntelligenceDB'
    '?driver=ODBC+Driver+17+for+SQL+Server'
    '&trusted_connection=yes'
    '&TrustServerCertificate=yes'
)

#  customers 
customers = df[['Customer ID', 'Customer Since']].drop_duplicates(subset='Customer ID').dropna()
customers.columns = ['customer_id', 'customer_since']
customers['customer_id'] = customers['customer_id'].astype(int)
customers.to_sql('customers', engine, if_exists='append', index=False)
print("customers loaded:", len(customers))

#  products 

products = df[['sku', 'category_name_1']].dropna()
products.columns = ['sku', 'category']
products['sku'] = products['sku'].str.strip().str.lower()  # normalize casing and whitespace
products['category'] = products['category'].str.strip()
products = products.drop_duplicates(subset='sku', keep='first')
products = products.reset_index(drop=True)
print("Unique SKUs:", len(products))
products.to_sql('products', engine, if_exists='append', index=False)
print("products loaded:", len(products))
#  payments 
payments = df[['payment_method']].drop_duplicates().dropna()
payments.to_sql('payments', engine, if_exists='append', index=False)
print("payments loaded:", len(payments))

#  dates 
dates = df[['created_at','Year','Month','order_quarter','day_of_week','M-Y','FY']].drop_duplicates(subset='created_at').dropna()
dates.columns = ['date_id','year','month','quarter','day_of_week','month_year','fiscal_year']
dates['date_id'] = pd.to_datetime(dates['date_id']).dt.date
dates.to_sql('dates', engine, if_exists='append', index=False)
print("dates loaded:", len(dates))

#  sales 
sales = df[[
    'item_id','increment_id','Customer ID','sku','payment_method',
    'created_at','status','status_grouped','price','qty_ordered',
    'grand_total','discount_amount','discount_pct','revenue_per_unit',
    'is_return','BI Status'
]].copy()

sales.columns = [
    'item_id','increment_id','customer_id','sku','payment_method',
    'order_date','status','status_grouped','price','qty_ordered',
    'grand_total','discount_amount','discount_pct','revenue_per_unit',
    'is_return','bi_status'
]

sales['customer_id'] = sales['customer_id'].astype('Int64')
sales['order_date'] = pd.to_datetime(sales['order_date']).dt.date
sales['is_return'] = sales['is_return'].astype(int)
sales['sku'] = sales['sku'].str.strip().str.lower()
sales['item_id'] = sales['item_id'].astype('Int64')
sales['increment_id'] = pd.to_numeric(sales['increment_id'], errors='coerce').astype('Int64')  # add this
sales = sales.drop_duplicates(subset='item_id', keep='first')
sales = sales.dropna(subset=['item_id'])
print("Sales rows to insert:", len(sales))

sales.to_sql('sales', engine, if_exists='append', index=False, chunksize=5000)
print("sales loaded:", len(sales))
print("\nAll tables loaded successfully!")