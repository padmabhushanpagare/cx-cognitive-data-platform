import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sqlalchemy import create_engine
import os

# --- ENVIRONMENT CONFIGURATION ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cx_secret_password")
DB_NAME = os.getenv("DB_NAME", "cx_platform")

# Create SQLAlchemy Engine for Pandas
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

def analyze_root_causes():
    print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")
    
    # Query all user messages
    query = "SELECT user_message FROM conversation_logs;"
    df = pd.read_sql(query, engine)

    if len(df) < 5:
        print("Not enough data to analyze. Please chat with the AI a few more times.")
        return

    print(f"Analyzing {len(df)} customer messages...")

    # 1. Vectorize the text (convert words to numbers)
    vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
    X = vectorizer.fit_transform(df['user_message'])

    # 2. Use K-Means to find 3 hidden topics (clusters)
    num_clusters = 3
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(X)

    # 3. Extract the top words for each cluster
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()

    print("\n--- ROOT CAUSE INTELLIGENCE REPORT ---")
    for i in range(num_clusters):
        print(f"\nTopic #{i+1}:")
        print("Keywords: ", end="")
        for ind in order_centroids[i, :5]:
            print(f"'{terms[ind]}'", end=" ")
        print()

        # Find examples of messages in this cluster
        cluster_messages = df[kmeans.labels_ == i]['user_message'].head(3).tolist()
        print("Example messages:")
        for msg in cluster_messages:
            print(f"  - {msg}")

    # 4. Cross-reference with Order Data
    print("\n--- OPERATIONAL CORRELATION ---")
    order_query = "SELECT status, COUNT(*) as count FROM fact_orders GROUP BY status ORDER BY count DESC;"
    order_df = pd.read_sql(order_query, engine)
    
    print("Order Status Bottlenecks (What might be driving contacts):")
    print(order_df.to_string(index=False))

if __name__ == "__main__":
    analyze_root_causes()