import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="CX Analytics Dashboard", layout="wide")
st.title("📊 Executive CX Analytics Dashboard")
st.markdown("Real-time operational metrics extracted from AI interactions.")

# Database connection
def get_data():
    conn = psycopg2.connect(
        host="localhost", port="5434", user="admin", 
        password="cx_secret_password", dbname="cx_platform"
    )
    query = "SELECT * FROM conversation_logs ORDER BY timestamp DESC;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

try:
    df = get_data()
    
    # 1. Top Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total AI Interactions", len(df))
    
    escalations = df['escalated'].sum() if len(df) > 0 else 0
    col2.metric("Human Handoffs", escalations)
    
    if len(df) > 0:
        automation_rate = ((len(df) - escalations) / len(df)) * 100
        col3.metric("Automation Rate", f"{automation_rate:.1f}%")
    else:
        col3.metric("Automation Rate", "N/A")
        
    # 2. Data Table
    st.subheader("Recent Interactions")
    st.dataframe(df[['timestamp', 'user_message', 'ai_response', 'escalated']])
    
    # 3. Simple Analysis
    if len(df) > 0:
        st.subheader("Handoff Analysis")
        st.bar_chart(df['escalated'].value_counts())

except Exception as e:
    st.error(f"Could not load data from database. Did you run the FastAPI server and send a message first? Error: {e}")
