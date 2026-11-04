import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
# Default to localhost for local testing, but use Docker service name when inside Docker
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_chat_model():
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Chat Model (Cloud)")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        print(f"[FACTORY] Initializing Llama 3 Chat Model at {OLLAMA_BASE_URL}")
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3.1", temperature=0, base_url=OLLAMA_BASE_URL)

def get_embedding_model():
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Embeddings (Cloud)")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        print(f"[FACTORY] Initializing Ollama Embeddings at {OLLAMA_BASE_URL}")
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)