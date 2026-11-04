import os
import pandas as pd
from langchain_core.documents import Document
from langchain_chroma import Chroma
from llm_factory import get_embedding_model  # <--- USE THE FACTORY

# 1. Load the clean data
# Use environment variable if inside Docker, otherwise fallback to relative path
CSV_PATH = os.getenv("CSV_PATH", "../01_data_ingestion/raw_data/books_raw.csv")
print(f"Loading data from {CSV_PATH}...")
df = pd.read_csv(CSV_PATH)

# 2. Convert rows to LangChain Document objects
documents = []
for index, row in df.iterrows():
    content = f"Book Title: {row['title']}. Price: {row['price']}. Availability: {row['availability']}."
    metadata = {"title": row['title'], "price": row['price']}
    documents.append(Document(page_content=content, metadata=metadata))

print(f"Converted {len(documents)} rows to documents.")

# 3. Create Embeddings and Store in ChromaDB
print("Generating embeddings...")
embeddings = get_embedding_model() # <--- FACTORY DECIDES WHICH ONE

vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("Success! Vector database built and saved to ./chroma_db")