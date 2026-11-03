import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

# Read the provider from the .env file. Default to 'ollama' if not set.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

def get_chat_model():
    """Returns the chat model based on the environment configuration."""
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Chat Model (Cloud)")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        print("[FACTORY] Initializing Llama 3 Chat Model (On-Premise)")
        return ChatOllama(model="llama3.1", temperature=0)

def get_embedding_model():
    """Returns the embedding model based on the environment configuration."""
    if LLM_PROVIDER == "openai":
        print("[FACTORY] Initializing OpenAI Embeddings (Cloud)")
        return OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        print("[FACTORY] Initializing Ollama Embeddings (On-Premise)")
        return OllamaEmbeddings(model="nomic-embed-text")
