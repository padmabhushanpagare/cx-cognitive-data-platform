import streamlit as st
import pandas as pd
import psycopg2
import os
from sqlalchemy import create_engine

st.set_page_config(page_title="CX Analytics Dashboard", layout="wide")
st.title("📊 Executive CX Operations Dashboard")

# --- ENVIRONMENT CONFIGURATION ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cx_secret_password")
DB_NAME = os.getenv("DB_NAME", "cx_platform")

# SQLAlchemy engine for Pandas (fixes UserWarning)
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

def get_data(query):
    """Fetch data using SQLAlchemy engine."""
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Database read failed: {e}")
        return pd.DataFrame()

def execute_write(query, params=None):
    """Execute a write operation using psycopg2."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, 
            password=DB_PASSWORD, dbname=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database write failed: {e}")
        return False

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Analytics Overview", "🎧 Supervisor Handoff Queue", "🕵️ AI Quality Assurance", "🧠 Root Cause Intelligence"])

# ==========================================
# TAB 1: ANALYTICS OVERVIEW
# ==========================================
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

# ==========================================
# TAB 2: SUPERVISOR HANDOFF QUEUE
# ==========================================
with tab2:
    st.header("Open Handoff Tickets")
    st.markdown("These tickets were escalated by the ML Router or LLM and require a human agent.")
    
    handoff_df = get_data("SELECT ticket_id, customer_message, status, created_at FROM fact_handoffs WHERE status = 'OPEN' ORDER BY created_at ASC;")
    
    if not handoff_df.empty:
        for _, row in handoff_df.iterrows():
            with st.expander(f"Ticket #{row['ticket_id']} - {row['created_at']}"):
                st.write(f"**Customer Message:** {row['customer_message']}")
                
                if st.button(f"Resolve Ticket #{row['ticket_id']}", key=f"resolve_{row['ticket_id']}"):
                    if execute_write("UPDATE fact_handoffs SET status = 'RESOLVED' WHERE ticket_id = %s", (row['ticket_id'],)):
                        st.success(f"Ticket #{row['ticket_id']} Resolved!")
                        st.rerun()
    else:
        st.success("🎉 No open tickets! The AI has handled everything.")

# ==========================================
# TAB 3: AI QUALITY ASSURANCE
# ==========================================
with tab3:
    st.header("Automated Quality Assurance Scores")
    st.markdown("This AI evaluates 100% of interactions against compliance and empathy rubrics.")
    
    # Join with human reviews to show the full picture
    qa_df = get_data("""
        SELECT q.score_id, q.log_id, c.user_message, c.ai_response, 
               q.overall_score AS ai_score, q.qa_feedback AS ai_feedback, 
               q.requires_human_review,
               h.human_score, h.human_feedback, h.reviewed_at
        FROM fact_quality_scores q
        JOIN conversation_logs c ON q.log_id = c.id
        LEFT JOIN fact_human_qa_reviews h ON q.score_id = h.score_id
        ORDER BY q.evaluated_at DESC;
    """)
    
    if not qa_df.empty:
        for _, row in qa_df.iterrows():
            with st.expander(f"Log #{row['log_id']} - AI Score: {row['ai_score']}/5"):
                st.write(f"**Customer:** {row['user_message']}")
                st.write(f"**AI Agent:** {row['ai_response']}")
                st.info(f"**AI QA Feedback:** {row['ai_feedback']}")
                
                # Check if a human has already reviewed this
                if pd.notna(row['human_score']):
                    st.success(f"**Human Override:** {row['human_score']}/5")
                    st.write(f"**Supervisor Comments:** {row['human_feedback']}")
                else:
                    st.markdown("### Human Supervisor Review")
                    human_score = st.slider("Override Score (1-5)", 1, 5, int(row['ai_score']), key=f"slider_{row['score_id']}")
                    human_feedback = st.text_input("Supervisor Comments", key=f"text_{row['score_id']}")
                    
                    if st.button("Submit Human Override", key=f"btn_{row['score_id']}"):
                        # INSERT into audit table instead of UPDATE
                        query = """
                            INSERT INTO fact_human_qa_reviews (score_id, human_score, human_feedback) 
                            VALUES (%s, %s, %s)
                        """
                        if execute_write(query, (row['score_id'], human_score, human_feedback)):
                            st.success("Human override saved to audit trail!")
                            st.rerun()
    else:
        st.info("No QA scores found. Run the QA evaluator script.")

# ==========================================
# TAB 4: ROOT CAUSE INTELLIGENCE
# ==========================================
with tab4:
    st.header("🧠 Root Cause Intelligence")
    st.markdown("These are the top contact drivers extracted from customer conversations via NLP clustering.")
    
    if st.button("Run Root Cause Analysis"):
        with st.spinner("Analyzing NLP clusters..."):
            try:
                df_logs = get_data("SELECT user_message FROM conversation_logs;")
                if len(df_logs) >= 5:
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.cluster import KMeans
                    
                    vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
                    X = vectorizer.fit_transform(df_logs['user_message'])
                    
                    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                    kmeans.fit(X)
                    
                    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
                    terms = vectorizer.get_feature_names_out()
                    
                    for i in range(3):
                        with st.expander(f"Topic #{i+1}"):
                            keywords = [terms[ind] for ind in order_centroids[i, :5]]
                            st.write(f"**Keywords:** {', '.join(keywords)}")
                            examples = df_logs[kmeans.labels_ == i]['user_message'].head(3).tolist()
                            st.write("**Examples:**")
                            for ex in examples:
                                st.write(f"- {ex}")
                else:
                    st.warning("Not enough chat logs to analyze. Send at least 5 messages in the chat UI.")
            except Exception as e:
                st.error(f"Failed to run analysis: {e}")