from google import genai
import pandas as pd
from sqlalchemy import create_engine, text

#  Gemini configuration
client =genai.Client(api_key="YOUR-API-KEY-HERE")


# SQL Server connection
engine = create_engine(
    'mssql+pyodbc://.\\SQLEXPRESS/SalesIntelligenceDB'
    '?driver=ODBC+Driver+17+for+SQL+Server'
    '&trusted_connection=yes'
    '&TrustServerCertificate=yes'
)

print("Setup complete. Gemini and SQL Server connected.")

SCHEMA_CONTEXT = """
You are a SQL expert working with a Microsoft SQL Server database called SalesIntelligenceDB.

Here are the tables and their columns:

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

status_grouped values are: completed, cancelled, refunded, pending, on_hold, fraud

Write only a single valid T-SQL SELECT query to answer the user's question.
Do not include any explanation, markdown formatting, or backticks.
Only return the raw SQL query.
Never write INSERT, UPDATE, DELETE, DROP, or ALTER statements.
"""

print("Schema context defined.")


def ask_question(user_question):
    print(f"\nQuestion: {user_question}")
    
    #  Gemini  write the SQL
    prompt = f"{SCHEMA_CONTEXT}\n\nUser question: {user_question}\n\nSQL query:"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    sql_query = response.text.strip()
    
    # formatting 
    sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
    
    print(f"\nGenerated SQL:\n{sql_query}")
    
    #  Safety check before running
    forbidden_words = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'EXEC']
    if any(word in sql_query.upper() for word in forbidden_words):
        return "Blocked: This query contains a forbidden operation and was not executed."
    
    # Executing the query 
    try:
        with engine.connect() as conn:
            result_df = pd.read_sql(text(sql_query), conn)
    except Exception as e:
        return f"Error executing query: {e}"
    
    print(f"\nQuery Result:\n{result_df}")
    
    #  Gemini explain the result in plain English
    explain_prompt = f"""
    The user asked: {user_question}
    The SQL query returned this data:
    {result_df.to_string(index=False)}
    
    Write a short, clear, 2-3 sentence answer in plain English based on this data.
    Do not mention SQL or databases. Just answer like a data analyst would.
    """
    final_answer = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=explain_prompt
    )

    print(f"\nAnswer:\n{final_answer.text}")
    return final_answer.text


# Testing

#ask_question("What was the total revenue in 2018?")
#ask_question("Which payment method has the most cancelled orders?")
#ask_question("Who are the top 3 customers by total spend?")
ask_question("What are the total number of orders made")