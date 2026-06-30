import numpy as np
import pandas as pd

#reading dataset
sales=pd.read_csv('Pakistan Largest Ecommerce Dataset.csv')

#dropping unnecessary columns and rows
sales.drop(columns=['Unnamed: 21','Unnamed: 22','Unnamed: 23','Unnamed: 24','Unnamed: 25'], inplace=True)
sales.dropna(subset=['item_id', 'grand_total', 'created_at', 'Customer ID'], how='all', inplace=True)

#fix dtypes
sales['created_at'] = pd.to_datetime(sales['created_at'], errors='coerce')
sales['Working Date'] = pd.to_datetime(sales['Working Date'], errors='coerce')
sales['Customer Since'] = pd.to_datetime(sales['Customer Since'], errors='coerce')

sales['grand_total'] = pd.to_numeric(sales['grand_total'], errors='coerce')
sales['price'] = pd.to_numeric(sales['price'], errors='coerce')
sales['qty_ordered'] = pd.to_numeric(sales['qty_ordered'], errors='coerce')
sales['discount_amount'] = pd.to_numeric(sales['discount_amount'], errors='coerce')
sales['Customer ID'] = pd.to_numeric(sales['Customer ID'], errors='coerce')

#replacing null for status
sales['status']=sales['status'].replace('\\N',np.nan)

status_map = {
    'complete': 'completed',
    'closed': 'completed',
    'paid': 'completed',
    'received': 'completed',
    'canceled': 'cancelled',
    'order_refunded': 'refunded',
    'refund': 'refunded',
    'exchange': 'refunded',
    'fraud': 'fraud',
    'holded': 'on_hold',
    'pending': 'pending',
    'pending_paypal': 'pending',
    'processing': 'pending',
    'payment_review': 'pending',
    'cod': 'pending',
    'cashatdoorstep': 'pending'
}

sales['status_grouped']=sales['status'].map(status_map)

sales['is_return'] = sales['grand_total'] < 0

df_sales = sales[sales['grand_total'] > 0].copy()


df_sales.dropna(subset=['grand_total', 'created_at', 'category_name_1'], inplace=True)
df_sales['category_name_1'] = df_sales['category_name_1'].replace('\\N', np.nan)
df_sales.dropna(subset=['category_name_1'], inplace=True)


df_sales['order_month'] = df_sales['created_at'].dt.to_period('M')
df_sales['order_year'] = df_sales['created_at'].dt.year
df_sales['order_quarter'] = df_sales['created_at'].dt.quarter
df_sales['day_of_week'] = df_sales['created_at'].dt.day_name()

# Revenue per item
df_sales['revenue_per_unit'] = df_sales['grand_total'] / df_sales['qty_ordered'].replace(0, np.nan)

# Discount percentage
df_sales['discount_pct'] = (df_sales['discount_amount'] / (df_sales['grand_total'] + df_sales['discount_amount'])) * 100

print("Final shape:", df_sales.shape)
print("Null counts:\n", df_sales.isnull().sum())
print("Date range:", df_sales['created_at'].min(), "to", df_sales['created_at'].max())
print("Categories:\n", df_sales['category_name_1'].value_counts())
print("Status groups:\n", df_sales['status_grouped'].value_counts())



df_sales.dropna(subset=['status', 'Customer ID', 'sku'], inplace=True)
df_sales.drop(columns=['sales_commission_code'], inplace=True)

# Save
df_sales.to_csv('cleaned_ecommerce_data.csv', index=False)
print("Done! Final shape:", df_sales.shape)