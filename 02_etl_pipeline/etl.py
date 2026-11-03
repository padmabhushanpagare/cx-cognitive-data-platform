import pandas as pd
import psycopg2
from psycopg2 import sql
import os

# 1. DATABASE CONFIGURATION (Using your port 5434)
DB_HOST = "localhost"
DB_PORT = "5434"
DB_USER = "admin"
DB_PASSWORD = "cx_secret_password"
DB_NAME = "cx_platform"

# 2. PATH TO THE RAW DATA (Notice we go up one folder and into the ingestion folder)
CSV_PATH = "../01_data_ingestion/raw_data/books_raw.csv"

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_table(cursor):
    """Creates the raw table if it doesn't exist."""
    # We use VARCHAR for now. In the next phase, we will refine this.
    create_table_query = """
    CREATE TABLE IF NOT EXISTS raw_books (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        price VARCHAR(50),
        availability VARCHAR(100)
    );
    """
    cursor.execute(create_table_query)
    print("Table 'raw_books' is ready.")

def extract_and_load():
    print("Starting ETL Pipeline...")
    
    # EXTRACT: Read the CSV
    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find {CSV_PATH}. Did you run the scraper?")
        return
        
    df = pd.read_csv(CSV_PATH)
    print(f"Extracted {len(df)} rows from CSV.")
    
    # TRANSFORM: Clean the data
    # Right now, price looks like "£51.77". Let's keep it as a string for the RAW table, 
    # but strip whitespace just in case.
    df['title'] = df['title'].str.strip()
    # Fix the encoding issue and remove currency symbols for numeric parsing
    df['price'] = df['price'].str.replace('Â', '', regex=False).str.replace('£', '', regex=False).str.strip()
    df['availability'] = df['availability'].str.strip()

    # LOAD: Insert into Database
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    
    try:
        # Create the table structure
        # Fix the encoding issue and remove currency symbols for numeric parsing
        df['price'] = df['price'].str.replace('Â', '', regex=False).str.replace('£', '', regex=False).str.strip()        
        
        create_table(cursor)
        
        # Clear out old data so we don't get duplicates if we run this twice
        cursor.execute("TRUNCATE TABLE raw_books RESTART IDENTITY;")
        
        # Insert data row by row
        insert_query = """
        INSERT INTO raw_books (title, price, availability) 
        VALUES (%s, %s, %s);
        """
        
        # Convert the Pandas DataFrame into a list of tuples for the database
        records = df[['title', 'price', 'availability']].values.tolist()
        
        # Execute the insert for all records
        cursor.executemany(insert_query, records)
        
        # Commit the transaction (save the changes)
        conn.commit()
        print(f"Successfully loaded {len(records)} records into PostgreSQL.")
        
    except Exception as e:
        print(f"An error occurred during ETL: {e}")
        conn.rollback() # Undo changes if something broke
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    extract_and_load()
