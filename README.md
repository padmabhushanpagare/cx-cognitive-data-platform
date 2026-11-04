# Enterprise CX Cognitive Data Platform

## 📖 Executive Summary
An enterprise-grade, full-stack AI platform designed for Business Process Outsourcing (BPO) and Customer Experience (CX) operations. This system demonstrates the end-to-end lifecycle of an AI product: from unstructured data crawling and ETL pipelines to on-premise LLM deployment, autonomous agent tool-calling, human handoff routing, and executive analytics.

## 🏗️ System Architecture

The platform is built as six interconnected, modular microservices:

1. **Data Ingestion (`01_data_ingestion`):** Python-based web crawler that extracts unstructured data (HTML) and converts it to structured CSV files.
2. **ETL Pipeline (`02_etl_pipeline`):** Pandas and psycopg2 scripts that clean raw data, handle encoding issues, and load it into a PostgreSQL relational database.
3. **AI Agent Core (`03_ai_agent_core`):** A LangGraph-based state machine agent. It uses a local Llama 3.1 model (via Ollama) for zero-cost, privacy-compliant inference. It includes a vector database (ChromaDB) for semantic search and a custom tool to trigger human handoffs.
4. **Full-Stack App (`04_fullstack_app`):** A FastAPI backend and Streamlit frontend. Includes a customer chat UI and an Executive Analytics Dashboard that reads live SQL metrics.
5. **On-Prem Inference (`05_onprem_inference`):** Designed for strict data privacy. Uses quantized open-source models (Llama 3.1 8B) to eliminate reliance on third-party cloud APIs (OpenAI) while maintaining high reasoning capabilities.
6. **Evaluation Framework (`06_eval_framework`):** A Pytest-based automated reliability suite. Tests the agent for tool-calling accuracy, human handoff precision, and hallucination prevention.

## 🗺️ Azure Enterprise Deployment Mapping
While this MVP runs locally for development, here is exactly how it maps to the Azure Enterprise Ecosystem required in the JD:

| Local Component (MVP) | Azure Enterprise Equivalent | Purpose |
| :--- | :--- | :--- |
| **Python Scraper / Pandas** | **Azure Data Factory (ADF)** | Orchestrating ingestion from external client APIs/websites. |
| **PostgreSQL (Docker)** | **Azure Synapse Analytics (SQL DW)** | Serving as the data warehouse for Fact and Dimension tables. |
| **ChromaDB** | **Azure AI Search (Vector DB)** | Enterprise-grade semantic search and RAG indexing. |
| **Local Spark (Emulated)** | **Azure Databricks (PySpark)** | Large-scale data transformation and NLP batch processing. |
| **Ollama (Llama 3.1)** | **Azure ML / On-Prem GPU Servers** | Hosting fine-tuned models for secure, high-throughput inference. |
| **FastAPI + Streamlit** | **Azure App Service / AKS** | Hosting the frontend and backend REST APIs. |

## ⚙️ How to Run Locally

1. **Start the Database:**
   `docker compose up -d`
2. **Rebuild the Vector DB (Optional):**
   `cd 03_ai_agent_core && python build_knowledge_base.py`
3. **Start the API Backend:**
   `cd 03_ai_agent_core && uvicorn api:app --port 8000`
4. **Start the Chat UI:**
   `cd 04_fullstack_app && streamlit run app.py`
5. **Start the Analytics Dashboard:**
   `cd 04_fullstack_app && streamlit run dashboard.py --server.port 8502`
6. **Run the Evaluation Tests:**
   `cd 06_eval_framework && pytest -v -s test_reliability.py`

## 🛠️ Tech Stack
* **AI/ML:** LangGraph, LangChain, Ollama (Llama 3.1), HuggingFace
* **Data:** Python, Pandas, PostgreSQL, ChromaDB
* **Backend:** FastAPI, Pydantic, Uvicorn
* **Frontend:** Streamlit
* **Testing:** Pytest
* **Infrastructure:** Docker, Docker Compose