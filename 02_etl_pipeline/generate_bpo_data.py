import pandas as pd
import random
from datetime import datetime, timedelta
import os

print("Generating synthetic BPO e-commerce data...")

# 1. Generate Customers (Dimension Table)
first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
last_names = ["Smith", "Doe", "Johnson", "Brown", "Taylor", "Anderson"]
customers = []
for i in range(1, 21):
    customers.append({
        "customer_id": f"CUST-{1000 + i}",
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "email": f"user{i}@example.com",
        "tier": random.choice(["Standard", "Premium", "VIP"])
    })
df_customers = pd.DataFrame(customers)

# 2. Generate Orders (Fact Table)
statuses = ["Processing", "Shipped", "Delivered", "Delayed", "Lost"]
orders = []
for i in range(1, 51):
    customer = random.choice(customers)
    status = random.choice(statuses)
    order_date = datetime.now() - timedelta(days=random.randint(1, 30))
    
    orders.append({
        "order_id": f"ORD-{5000 + i}",
        "customer_id": customer["customer_id"],
        "status": status,
        "amount": round(random.uniform(20.0, 500.0), 2),
        "order_date": order_date.strftime("%Y-%m-%d")
    })
df_orders = pd.DataFrame(orders)

# 3. Save to CSV
os.makedirs('bpo_data', exist_ok=True)
df_customers.to_csv('bpo_data/customers.csv', index=False)
df_orders.to_csv('bpo_data/orders.csv', index=False)

print("Data generated! Saved to bpo_data/customers.csv and bpo_data/orders.csv")
