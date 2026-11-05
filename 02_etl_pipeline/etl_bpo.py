import pandas as pd
import psycopg2

# Database connection
conn = psycopg2.connect(
    host="localhost", port="5434", user="admin", 
    password="cx_secret_password", dbname="cx_platform"
)
cursor = conn.cursor()

print("Creating Star Schema tables...")

# 1. Create Dimension Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        tier VARCHAR(50)
    );
    CREATE TABLE IF NOT EXISTS fact_orders (
        order_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) REFERENCES dim_customers(customer_id),
        status VARCHAR(50),
        amount DECIMAL(10, 2),
        order_date DATE
    );
    CREATE TABLE IF NOT EXISTS fact_handoffs (
        ticket_id SERIAL PRIMARY KEY,
        customer_message TEXT,
        status VARCHAR(50) DEFAULT 'OPEN',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
# Before inserting, clean old data (except handoffs)
cursor.execute("TRUNCATE TABLE fact_orders, dim_customers CASCADE;")

# 4. Load Data
print("Loading data into database...")
df_customers = pd.read_csv('bpo_data/customers.csv')
df_orders = pd.read_csv('bpo_data/orders.csv')

# Insert Customers
for _, row in df_customers.iterrows():
    cursor.execute(
        "INSERT INTO dim_customers (customer_id, name, email, tier) VALUES (%s, %s, %s, %s)",
        (row['customer_id'], row['name'], row['email'], row['tier'])
    )

# Insert Orders
for _, row in df_orders.iterrows():
    cursor.execute(
        "INSERT INTO fact_orders (order_id, customer_id, status, amount, order_date) VALUES (%s, %s, %s, %s, %s)",
        (row['order_id'], row['customer_id'], row['status'], row['amount'], row['order_date'])
    )

conn.commit()
cursor.close()
conn.close()
print("Star Schema successfully loaded into PostgreSQL!")

