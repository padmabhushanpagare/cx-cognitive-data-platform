import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(page_title="CX Analytics Dashboard", layout="wide")
st.title("📊 Executive CX Operations Dashboard")

# Read DB config from Environment Variables (Docker) or default to localhost
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")

def get_data(query):
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user="admin", 
            password="cx_secret_password", dbname="cx_platform"
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

# --- TABS ---
tab1, tab2 = st.tabs(["📈 Analytics Overview", "🎧 Supervisor Handoff Queue"])

with tab1:
    st.header("Operational Metrics")
    df = get_data("SELECT * FROM conversation_logs ORDER BY timestamp DESC;")
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total AI Interactions", len(df))
        escalations = df['escalated'].sum()
        col2.metric("Human Handoffs", escalations)
        
        automation_rate = ((len(df) - escalations) / len(df)) * 100 if len(df) > 0 else 0
        col3.metric("Automation Rate", f"{automation_rate:.1f}%")
        
        st.subheader("Recent Interactions")
        st.dataframe(df[['timestamp', 'user_message', 'ai_response', 'escalated']])
    else:
        st.info("No interactions logged yet.")

with tab2:
    st.header("Open Handoff Tickets")
    st.markdown("These tickets were escalated by the ML Router and require a human agent.")
    
    # Query the handoffs table
    handoff_df = get_data("SELECT ticket_id, customer_message, status, created_at FROM fact_handoffs WHERE status = 'OPEN' ORDER BY created_at ASC;")
    
    if not handoff_df.empty:
        for index, row in handoff_df.iterrows():
            with st.expander(f"Ticket #{row['ticket_id']} - {row['created_at']}"):
                st.write(f"**Customer Message:** {row['customer_message']}")
                
                # Add a button to resolve the ticket
                if st.button(f"Resolve Ticket #{row['ticket_id']}", key=row['ticket_id']):
                    try:
                        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user="admin", password="cx_secret_password", dbname="cx_platform")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE fact_handoffs SET status = 'RESOLVED' WHERE ticket_id = %s", (row['ticket_id'],))
                        conn.commit()
                        conn.close()
                        st.success(f"Ticket #{row['ticket_id']} Resolved!")
                        st.rerun() # Refresh the page
                    except Exception as e:
                        st.error(f"Failed to update ticket: {e}")
    else:
        st.success("🎉 No open tickets! The AI has handled everything.")