# NexusFreight / FleetHarbor Logistics AI Chatbot

An enterprise-grade, Clean Architecture Logistics Support AI Chatbot powered by FastAPI, Hybrid RAG (ChromaDB + SQLite/PostgreSQL), SentenceTransformers, and Groq LLM inference for accurate shipment tracking, employee lookup, customs guidance, and operational policy Q&A.

## Key Technologies
- **Architecture:** Clean Architecture (`presentation` → `application` → `domain` ← `infrastructure`)
- **API & Web UI:** FastAPI + Uvicorn + decoupled `frontend/` HTML/CSS/JS SPA
- **Vector Database:** ChromaDB (`PersistentClient` at `data/chroma_db/`, `1,155` indexed chunks)
- **Relational Persistence:** Local SQLite (`data/raw/shipments.db`, 19 tables / `89,634` rows) + optional Supabase PostgreSQL (`pgvector`)
- **Embeddings:** SentenceTransformers `all-MiniLM-L6-v2` (384 dimensions) with in-memory LRU cache
- **LLM Inference:** Groq API (`openai/gpt-oss-20b`) with exponential backoff, rate-limit handling, and SSE streaming
- **Testing:** Unified `pytest` suite (`tests/{unit,integration,api,e2e}` — `204 passed, 2 skipped` in `27.54s`) + Playwright E2E + 55-case classifier benchmark (`100.0%`)

---

## Project Directory Structure

```text
shipment_chatbot_project/
├── src/logistics_chatbot/
│   ├── __init__.py
│   ├── main.py                         # Canonical ASGI app, create_app(), serve()
│   ├── core/                           # config.py, constants.py, errors.py, logging.py
│   ├── domain/                         # Pure entities, exceptions, repository interfaces
│   ├── application/
│   │   ├── services/                   # chat_service, shipment_service, employee_service, document_service
│   │   ├── chatbot/                    # classifier, conversation, deterministic_responses, response_formatter, orchestrator
│   │   ├── rag/                        # hybrid_search, retriever, context_builder
│   │   ├── ingestion/                  # document_processor, csv_processor, kb_loader
│   │   └── prompts/                    # system_prompt.py
│   ├── infrastructure/
│   │   ├── database/                   # connection, sqlite_repository, postgres_repository, csv_fallback, repository
│   │   ├── vector_store/               # chroma_store, pgvector_store, supabase_rest
│   │   ├── llm/                        # groq_client.py
│   │   └── embeddings/                 # sentence_transformer.py
│   ├── presentation/api/               # app.py, dependencies.py, routes/*, schemas/*
│   └── utils/                          # helpers.py
├── frontend/
│   ├── templates/index.html            # FleetHarbor AI web UI template
│   └── static/{css/style.css, js/app.js, assets/}
├── data/
│   ├── raw/                            # shipments.db (19 tables), shipments.csv, shipments_seed.json
│   ├── processed/                      # shipments.csv
│   ├── generated/                      # employees_roster.csv, customer_accounts.csv, global_hubs.csv
│   ├── knowledge_base/                 # kb_long.csv, kb_long.txt, knowledge_base.*, manuals/*.txt
│   ├── source_documents/               # Reference PDFs + Data_attach2.xlsx
│   ├── sql/                            # Seed SQL files
│   ├── uploads/                        # Upload staging directory
│   └── chroma_db/                      # Persistent ChromaDB vector store
├── migrations/sql/                     # schema.sql, schema_v2_enterprise.sql
├── docs/
│   ├── architecture/schema_mapping_v2.md
│   └── reports/                        # Integration reports (Markdown / DOCX)
├── reports/                            # Runtime validation, benchmark & QA outputs
├── scripts/
│   ├── setup/                          # setup_database.py, test_connections.py
│   ├── ingestion/                      # ingest_documents.py, ingest_excel_supabase.py, ingest_new_pdfs.py, index_all_knowledge_base.py
│   ├── validation/                     # evaluate_chatbot_intelligence.py, verify_live_integration.py, audit_live_server.py, etc.
│   ├── benchmarks/                     # benchmark_performance.py
│   └── generators/                     # create_question_bank.py, generate_*.py
├── tests/
│   ├── conftest.py                     # Shared fixtures (TestClient, isolated ChromaDB, mocked LLM)
│   ├── api/                            # FastAPI route & contract tests
│   ├── unit/                           # Clean architecture boundaries, classifier, memory, retriever, services
│   ├── integration/                    # SQLite, ChromaDB, CSV ingestion, enterprise data & RAG pipeline tests
│   ├── e2e/                            # Playwright headless browser UI walkthrough
│   ├── evaluators/                     # data_validator.py, metrics.py, question_bank_runner.py
│   └── question_bank/                  # 12 domain evaluation JSON suites
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── .env.example
├── run_chatbot.py
└── run_server.py
```

---

## Installation & Setup

### 1. Install Dependencies & Editable Package
```bash
pip install -r requirements.txt
pip install -e . --no-build-isolation --no-deps
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env` in the project root and set at minimum `GROQ_API_KEY`:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
CHROMA_MODE=persistent
CHROMA_PERSIST_DIRECTORY=data/chroma_db
CHROMA_COLLECTION_NAME=logistics_knowledge_chunks
# Optional Supabase PostgreSQL connection string:
SUPABASE_DB_URL=
```
When `SUPABASE_DB_URL` is unset, the application operates in local mode backed by `data/raw/shipments.db` and persistent `data/chroma_db/`.

---

## Execution Guide

### 1. Diagnostic & Connectivity Check
```bash
python scripts/setup/test_connections.py
```

### 2. Launch FastAPI Server & Web UI
```bash
python run_server.py
# Or directly via Uvicorn:
uvicorn logistics_chatbot.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Chat UI:** `http://127.0.0.1:8000/`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **Health:** `GET /health`, `GET /api/health`, `GET /api/vector-db/health`
- **Chat:** `POST /chat`, `POST /chat/stream`, `POST /api/chat`
- **Shipments & Employees:** `GET /shipment/{id}`, `GET /api/shipments`, `GET /api/shipments/{shipment_id}`, `GET /employee/{id}`, `GET /employees`
- **Document / CSV Upload:** `POST /upload-doc`

### 3. Launch Interactive Terminal CLI
```bash
python run_chatbot.py
```

### 4. Run Automated Tests, Benchmarks & Validators
```bash
python -m pytest -q
python scripts/validation/evaluate_chatbot_intelligence.py
python scripts/benchmarks/benchmark_performance.py
python -m tests.evaluators.data_validator
```
