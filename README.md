# CX Cognitive Data Platform

## Overview
An enterprise-grade cognitive data solution and AI agent ecosystem designed for BPO (Business Process Outsourcing) customer experience operations. This platform ingests unstructured data, maintains structured ETL pipelines, and deploys LLM-based agents for customer interaction and human handoff.

## System Architecture
1. **Data Ingestion:** Scrapes unstructured CX data (FAQs, policies).
2. **ETL Pipeline:** Cleans data, generates Fact/Dimension tables (SQL/PySpark).
3. **AI Agent Core:** LangGraph-based autonomous agent with human handoff logic.
4. **Full-Stack App:** FastAPI backend and React dashboard for human supervisors.
5. **On-Prem Inference:** Local open-source model (quantized) for data privacy and cost efficiency.
6. **Evaluation Framework:** Pytest-based suite to measure hallucination, latency, and tool accuracy.

## Tech Stack
* **Data:** Python, Pandas, PySpark, PostgreSQL, ChromaDB
* **AI/ML:** LangGraph, HuggingFace, PyTorch, Ollama (Local LLM)
* **Infrastructure:** Docker, FastAPI, React
* **Testing:** Pytest, LangSmith (Tracing)

## Status
* [x] Project Initialization
* [ ] Month 1: Data Ingestion & ETL
* [ ] Month 2-3: Agent Core & Full-Stack
* [ ] Month 4: On-Prem Inference
* [ ] Month 5: Evaluation Framework
* [ ] Month 6: Azure Mapping & Documentation
