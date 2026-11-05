import os
import psycopg2

# Read config from environment variables (Docker) or fallback to localhost
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cx_secret_password")
DB_NAME = os.getenv("DB_NAME", "cx_platform")

def get_db_connection():
    """Centralized database connection factory."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
