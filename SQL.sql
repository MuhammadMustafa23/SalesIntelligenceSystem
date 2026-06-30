create database SalesIntelligenceDB 
use SalesIntelligenceDB

-- 1
CREATE TABLE customers (
    customer_id   BIGINT PRIMARY KEY,
    customer_since DATE
);

-- 2
CREATE TABLE products (
    sku       NVARCHAR(100) PRIMARY KEY,
    category  NVARCHAR(100)
);

-- 3
CREATE TABLE payments (
    payment_id     INT IDENTITY(1,1) PRIMARY KEY,
    payment_method NVARCHAR(100) UNIQUE
);

-- 4
CREATE TABLE dates (
    date_id      DATE PRIMARY KEY,
    year         INT,
    month        INT,
    quarter      INT,
    day_of_week  NVARCHAR(20),
    month_year   NVARCHAR(20),
    fiscal_year  NVARCHAR(20)
);

-- 5
CREATE TABLE sales (
    item_id          BIGINT PRIMARY KEY,
    increment_id     BIGINT,
    customer_id      BIGINT,
    sku              NVARCHAR(100),
    payment_method   NVARCHAR(100),
    order_date       DATE,
    status           NVARCHAR(50),
    status_grouped   NVARCHAR(50),
    price            DECIMAL(18,2),
    qty_ordered      INT,
    grand_total      DECIMAL(18,2),
    discount_amount  DECIMAL(18,2),
    discount_pct     DECIMAL(10,2),
    revenue_per_unit DECIMAL(18,2),
    is_return        BIT,
    bi_status        NVARCHAR(50),
    FOREIGN KEY (customer_id)    REFERENCES customers(customer_id),
    FOREIGN KEY (sku)            REFERENCES products(sku),
    FOREIGN KEY (payment_method) REFERENCES payments(payment_method),
    FOREIGN KEY (order_date)     REFERENCES dates(date_id)
);

--Monthly Revenue Trend
SELECT 
    d.year,
    d.month,
    d.month_year,
    SUM(s.grand_total) AS total_revenue,
    COUNT(s.item_id) AS total_orders,
    SUM(s.qty_ordered) AS total_units_sold
FROM sales s
JOIN dates d ON s.order_date = d.date_id
WHERE s.status_grouped = 'completed'
GROUP BY d.year, d.month, d.month_year
ORDER BY d.year, d.month;

--Revenue By Category
SELECT 
    p.category,
    SUM(s.grand_total) AS total_revenue,
    COUNT(s.item_id) AS total_orders,
    ROUND(SUM(s.grand_total) * 100.0 / SUM(SUM(s.grand_total)) OVER(), 2) AS revenue_share_pct
FROM sales s
JOIN products p ON s.sku = p.sku
WHERE s.status_grouped = 'completed'
GROUP BY p.category
ORDER BY total_revenue DESC;

--Order Status Breakdown

SELECT 
    status_grouped,
    COUNT(item_id) AS total_orders,
    ROUND(COUNT(item_id) * 100.0 / SUM(COUNT(item_id)) OVER(), 2) AS percentage
FROM sales
GROUP BY status_grouped
ORDER BY total_orders DESC;


--Payment Method Analysis
SELECT 
    s.payment_method,
    COUNT(s.item_id) AS total_orders,
    SUM(s.grand_total) AS total_revenue,
    ROUND(COUNT(s.item_id) * 100.0 / SUM(COUNT(s.item_id)) OVER(), 2) AS order_share_pct
FROM sales s
WHERE s.status_grouped = 'completed'
GROUP BY s.payment_method
ORDER BY total_orders DESC;

--Top 10 Customers By Revenue
SELECT TOP 10
    s.customer_id,
    c.customer_since,
    COUNT(s.item_id) AS total_orders,
    SUM(s.grand_total) AS total_spent,
    AVG(s.grand_total) AS avg_order_value
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE s.status_grouped = 'completed'
GROUP BY s.customer_id, c.customer_since
ORDER BY total_spent DESC;

--yearly Revenue Comparision
SELECT 
    d.year,
    SUM(s.grand_total) AS total_revenue,
    COUNT(s.item_id) AS total_orders,
    AVG(s.grand_total) AS avg_order_value
FROM sales s
JOIN dates d ON s.order_date = d.date_id
WHERE s.status_grouped = 'completed'
GROUP BY d.year
ORDER BY d.year;

--Cancellation Rate By Category
SELECT 
    p.category,
    COUNT(s.item_id) AS total_orders,
    SUM(CASE WHEN s.status_grouped = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    ROUND(SUM(CASE WHEN s.status_grouped = 'cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(s.item_id), 2) AS cancellation_rate_pct
FROM sales s
JOIN products p ON s.sku = p.sku
GROUP BY p.category
ORDER BY cancellation_rate_pct DESC;

--Monthly Revenue By Category
select d.year,d.month,d.month_year,p.category,
sum(s.grand_total)as total_revenue
from sales s
join dates d on s.order_date=d.date_id
join products p on s.sku=p.sku
where s.status_grouped='completed'
group by d.year,d.month,d.month_year,p.category
order by d.year,d.month,total_revenue desc


--Average Order Value By Month
SELECT 
    d.month_year,
    d.year,
    d.month,
    ROUND(AVG(s.grand_total), 2) AS avg_order_value,
    ROUND(AVG(s.discount_pct), 2) AS avg_discount_pct
FROM sales s
JOIN dates d ON s.order_date = d.date_id
WHERE s.status_grouped = 'completed'
GROUP BY d.month_year, d.year, d.month
ORDER BY d.year, d.month;

--Customer Cohort Analysis

SELECT 
    YEAR(c.customer_since) AS cohort_year,
    MONTH(c.customer_since) AS cohort_month,
    COUNT(DISTINCT s.customer_id) AS total_customers,
    SUM(s.grand_total) AS total_revenue,
    ROUND(SUM(s.grand_total) / COUNT(DISTINCT s.customer_id), 2) AS revenue_per_customer
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
WHERE s.status_grouped = 'completed'
GROUP BY YEAR(c.customer_since), MONTH(c.customer_since)
ORDER BY cohort_year, cohort_month;


select * from revenue_forecast