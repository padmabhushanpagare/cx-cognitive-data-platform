import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

def get_chat_model():
    """Returns the chat model based on the environment configuration."""
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Chat Model (Cloud)")
        from langchain_openai import ChatOpenAI # <--- Imported only when needed
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        print("[FACTORY] Initializing Llama 3 Chat Model (On-Premise)")
        from langchain_ollama import ChatOllama # <--- Imported only when needed
        return ChatOllama(model="llama3.1", temperature=0)

def get_embedding_model():
    """Returns the embedding model based on the environment configuration."""
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Embeddings (Cloud)")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        print("[FACTORY] Initializing Ollama Embeddings (On-Premise)")
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")