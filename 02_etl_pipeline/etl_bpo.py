import pandas as pd
import psycopg2
import os

# --- CONFIGURATION ---
# Read from environment variables (Docker) or fallback to localhost for local testing
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cx_secret_password")
DB_NAME = os.getenv("DB_NAME", "cx_platform")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, 
        password=DB_PASSWORD, dbname=DB_NAME
    )

def run_etl():
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("Creating Star Schema tables if they do not exist...")
        
        # 1. Dimension Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_customers (
                customer_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                tier VARCHAR(50)
            );
        """)

        # 2. Fact Table (Orders)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_orders (
                order_id VARCHAR(50) PRIMARY KEY,
                customer_id VARCHAR(50) REFERENCES dim_customers(customer_id),
                status VARCHAR(50),
                amount DECIMAL(10, 2),
                order_date DATE
            );
        """)

        # 3. Fact Table (Handoffs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_handoffs (
                ticket_id SERIAL PRIMARY KEY,
                customer_message TEXT,
                status VARCHAR(50) DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Conversation Logs (Required by API and QA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id SERIAL PRIMARY KEY,
                user_message TEXT,
                ai_response TEXT,
                escalated BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. Fact Table (QA Scores)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_quality_scores (
                score_id SERIAL PRIMARY KEY,
                log_id INTEGER REFERENCES conversation_logs(id),
                overall_score INTEGER,
                resolution_score INTEGER,
                empathy_score INTEGER,
                policy_score INTEGER,
                requires_human_review BOOLEAN,
                qa_feedback TEXT,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. Fact Table (Human QA Overrides - Audit Trail)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fact_human_qa_reviews (
                review_id SERIAL PRIMARY KEY,
                score_id INTEGER REFERENCES fact_quality_scores(score_id),
                human_score INTEGER,
                human_feedback TEXT,
                reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # --- IDEMPOTENT DATA LOADING ---
        print("Loading data into database...")
        df_customers = pd.read_csv('bpo_data/customers.csv')
        df_orders = pd.read_csv('bpo_data/orders.csv')

        # Insert/Update Customers (Upsert)
        for _, row in df_customers.iterrows():
            cursor.execute("""
                INSERT INTO dim_customers (customer_id, name, email, tier) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    tier = EXCLUDED.tier;
            """, (row['customer_id'], row['name'], row['email'], row['tier']))

        # Insert/Update Orders (Upsert)
        for _, row in df_orders.iterrows():
            cursor.execute("""
                INSERT INTO fact_orders (order_id, customer_id, status, amount, order_date) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    customer_id = EXCLUDED.customer_id,
                    status = EXCLUDED.status,
                    amount = EXCLUDED.amount,
                    order_date = EXCLUDED.order_date;
            """, (row['order_id'], row['customer_id'], row['status'], row['amount'], row['order_date']))

        conn.commit()
        print("✅ Star Schema successfully loaded/updated in PostgreSQL (Idempotent)!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ ETL Failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_etl()