import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import os

# Read from environment variables. 
# Note: DB_PASSWORD has no default, so it will fail fast if not provided.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "cx_platform")

try:
    DB_POOL = psycopg2.pool.ThreadedConnectionPool(
        1, 10,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
except Exception as e:
    print(f"CRITICAL: Failed to initialize database connection pool. Check credentials. Error: {e}")
    DB_POOL = None

@contextmanager
def get_db_connection():
    if DB_POOL is None:
        raise ConnectionError("Database connection pool is not initialized.")
    
    conn = DB_POOL.getconn()
    try:
        yield conn
    finally:
        DB_POOL.putconn(conn)