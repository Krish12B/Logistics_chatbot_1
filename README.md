# AI-Powered Logistics Chatbot (FleetHarbor)

An enterprise-grade, backend-driven Logistics Support AI Chatbot utilizing Retrieval-Augmented Generation (RAG) to deliver accurate, grounded tracking, customs, delay, and operational policy guidance.

## 🚀 Key Technologies
- **Application Framework:** FastAPI & Uvicorn (REST API)
- **Primary Vector Database:** ChromaDB 1.5.9 (Local Persistent & Server HNSW Cosine Indexing)
- **Relational & Cloud Vector Database:** Supabase PostgreSQL with `pgvector`
- **Embedding Generation:** SentenceTransformers `all-MiniLM-L6-v2` (384 dimensions)
- **LLM Inference:** Groq API (`openai/gpt-oss-20b`) with exponential backoff & rate-limit handling
- **Testing:** Python `unittest` (84 automated tests, 100% passing)

---

## 📁 Project Architecture & Directory Structure

```text
shipment_chatbot_project/
│
├── data/                               # Project Datasets & Vector Storage
│   ├── raw/                            # Initial seed & raw tracking data
│   │   ├── shipments.csv               # 10 operational shipments
│   │   ├── shipments_seed.json
│   │   └── shipments.db
│   ├── processed/                      # Cleaned operational datasets
│   │   └── shipments.csv
│   ├── knowledge_base/                 # Logistics domain policies & FAQ corpus
│   │   ├── kb_long.csv                 # 2,194 domain knowledge articles
│   │   ├── kb_long.txt
│   │   ├── knowledge_base.csv
│   │   └── knowledge_base.json
│   └── chroma_db/                      # Local persistent ChromaDB vector store
│
├── docs/                               # Project Documentation & Architecture
│   ├── architecture/
│   │   ├── schema.sql                  # PostgreSQL & pgvector DDL
│   │   ├── backend_audit_report.md
│   │   ├── supabase_connection_report.md
│   │   ├── rag_integration_report.md
│   │   └── chroma_vector_db_report.md
│   └── README.md
│
├── scripts/                            # Operational & Diagnostic CLI Utilities
│   ├── ingest_documents.py             # Knowledge ingestion (Chroma & Supabase)
│   ├── setup_database.py               # Supabase schema migration executor
│   ├── setup_database.sql              # Supabase table DDL and RPC functions
│   ├── test_connections.py             # Diagnostic & connectivity check
│   ├── retrieval_demo.py               # RAG context preview tool
│   └── generate_kb.py                  # Knowledge base synthesis script
│
├── src/                                # Core Application Source Code
│   └── logistics_chatbot/
│       ├── __init__.py
│       ├── api/                        # REST API Layer
│       │   ├── __init__.py
│       │   ├── app.py                  # FastAPI entry point & health checks
│       │   └── routes/                 # Modular API route controllers
│       │       ├── __init__.py
│       │       ├── chat.py             # POST /api/chat
│       │       └── shipments.py        # GET /api/shipments
│       ├── core/                       # Core Configuration & Primitives
│       │   ├── __init__.py
│       │   ├── config.py               # Path-anchored environment configuration
│       │   ├── errors.py               # Typed exception hierarchy
│       │   └── prompts.py              # System prompt & grounding constraints
│       ├── chatbot/                    # Chatbot Orchestration & Memory
│       │   ├── __init__.py
│       │   ├── chatbot.py              # Dialogue manager & CLI interface
│       │   ├── conversation.py         # Multi-turn sliding window session memory
│       │   └── llm_client.py           # Groq client with retry engine
│       ├── rag/                        # RAG & Information Retrieval
│       │   ├── __init__.py
│       │   ├── embeddings.py           # Dense vector encoding (384-dim)
│       │   ├── ingestion.py            # CSV/JSON document parsing & loading
│       │   ├── knowledge_base.py       # Supabase pgvector search
│       │   └── retrieval.py            # Hybrid retrieval (SQL + Vector)
│       ├── vectorstores/               # Vector Store Connectors
│       │   ├── __init__.py
│       │   ├── chroma_db.py            # ChromaDB Persistent & HTTP client
│       │   └── supabase_db.py          # Supabase REST client
│       ├── database/                   # Relational Persistence
│       │   ├── __init__.py
│       │   └── database.py             # PostgreSQL connection pool & queries
│       ├── schemas/                    # Pydantic Request/Response Models
│       │   ├── __init__.py
│       │   └── models.py
│       └── utils/                      # Helper Functions
│           ├── __init__.py
│           └── helpers.py              # Hashing, date parsing, pgvector formats
│
├── tests/                              # Automated Test Suite (84 tests)
│   ├── __init__.py
│   ├── test_api.py                     # REST API endpoint tests
│   ├── test_chatbot.py                 # Chatbot behavioral & grounding tests
│   ├── test_chroma_db.py               # ChromaDB connection & vector search tests
│   ├── test_rag_integration.py         # End-to-end RAG scenarios (1-12)
│   └── test_supabase_connection.py     # Database connection & pooling tests
│
├── .env                                # Local secrets (ignored in Git)
├── .env.example                        # Template for environment configuration
├── .gitignore                          # Excludes .env, pycache, chroma_db
├── pyproject.toml                      # Modern packaging specification
├── requirements.txt                    # Python dependencies
├── run_chatbot.py                      # Root shortcut to launch interactive CLI
├── run_server.py                       # Root shortcut to start FastAPI server
└── README.md
```

---

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env` in the project root:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# ChromaDB Settings
CHROMA_MODE=persistent
CHROMA_PERSIST_DIRECTORY=data/chroma_db
CHROMA_COLLECTION_NAME=logistics_knowledge_chunks

# Supabase PostgreSQL (Optional for live cloud database)
SUPABASE_DB_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```
*(Note: If `SUPABASE_DB_URL` is omitted, the chatbot runs seamlessly in offline mode using `data/raw/shipments.csv` and ChromaDB).*

---

## ⚡ Execution Guide

### 1. Run Diagnostic & Connectivity Check
```bash
python scripts/test_connections.py
```

### 2. Ingest Knowledge into ChromaDB
```bash
# Ingest full knowledge base (2,194 articles)
python scripts/ingest_documents.py --target chroma

# Ingest test batch of 50 articles
python scripts/ingest_documents.py --target chroma --limit 50
```

### 3. Launch Interactive Terminal Chatbot
```bash
python run_chatbot.py
```
*Example questions:*
- `What is the status of SHP-10001?`
- `Why is SHP-10002 delayed?`
- `What documents are required for international customs?`

### 4. Start the FastAPI REST API Server
```bash
python run_server.py
```
- **API Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** `GET http://127.0.0.1:8000/api/health`
- **ChromaDB Health:** `GET http://127.0.0.1:8000/api/vector-db/health`
- **Chat Endpoint:** `POST http://127.0.0.1:8000/api/chat`

### 5. Run the Automated Test Suite
```bash
python -m unittest discover -s tests -v
```
**Results:** `84 passed, 0 failed, 2 skipped (cloud-only) in ~8.3 seconds`.
