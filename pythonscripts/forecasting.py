import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
from sqlalchemy import create_engine

engine = create_engine(
    'mssql+pyodbc://.\\SQLEXPRESS/SalesIntelligenceDB'
    '?driver=ODBC+Driver+17+for+SQL+Server'
    '&trusted_connection=yes'
    '&TrustServerCertificate=yes'
)

# retrieve monthly revenue from SQL Server 
query = """
    SELECT 
        d.year,
        d.month,
        d.month_year,
        SUM(s.grand_total) AS total_revenue
    FROM sales s
    JOIN dates d ON s.order_date = d.date_id
    WHERE s.status_grouped = 'completed'
    GROUP BY d.year, d.month, d.month_year
    ORDER BY d.year, d.month
"""

df = pd.read_sql(query, engine)
print("Monthly data pulled:")
print(df)

# Prophet requires columns named ds (date) and y (value)
df['ds'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
df['y'] = df['total_revenue']
prophet_df = df[['ds', 'y']].copy()

#  Building and Training Model 
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    seasonality_mode='multiplicative'
)
model.fit(prophet_df)
print("\nModel trained successfully!")

#  Forecast next 12 months 
future = model.make_future_dataframe(periods=12, freq='MS')
forecast = model.predict(future)

#  forecast results 
print("\nForecast for next 12 months:")
forecast_only = forecast[forecast['ds'] > prophet_df['ds'].max()]
print(forecast_only[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_string(index=False))

#  Saving forecast to SQL Server ---
forecast_save = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
forecast_save.columns = ['forecast_date', 'predicted_revenue', 'lower_bound', 'upper_bound']
forecast_save['is_actual'] = forecast_save['forecast_date'].isin(prophet_df['ds']).astype(int)
forecast_save.to_sql('revenue_forecast', engine, if_exists='replace', index=False)
print("\nForecast saved to SQL Server table: revenue_forecast")

#  Plots
fig = model.plot(forecast)
plt.title('Sales Revenue Forecast')
plt.xlabel('Date')
plt.ylabel('Revenue (PKR)')
plt.tight_layout()
plt.savefig('forecast_plot.png', dpi=150)
plt.show()
print("Plot saved as forecast_plot.png")


fig2 = model.plot_components(forecast)
plt.tight_layout()
plt.savefig('forecast_components.png', dpi=150)
plt.show()
print("Components plot saved as forecast_components.png")