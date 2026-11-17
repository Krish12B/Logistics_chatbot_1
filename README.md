# Shipment Support Chatbot (Backend)

A terminal chatbot that answers shipment questions using:
- a **SQLite database** for shipment records (status, location, route, customs, delays)
- a **knowledge base** (`data/knowledge_base.json`) of FAQ answers
- the **Groq API** (Llama 3.3 70B) to write the final reply

## Setup

1. Install the dependency: `pip install -r requirements.txt`
2. Get a free API key at https://console.groq.com and set it:
   - Windows (PowerShell): `$env:GROQ_API_KEY="your_key_here"`
   - Mac/Linux: `export GROQ_API_KEY="your_key_here"`

## Run the chatbot in the terminal

    python3 chatbot.py

Type a question such as `What is the status of SHP-10001?`, or `exit` to quit.

## Run the tests

    python3 -m unittest -v test_chatbot

The tests use a fake LLM, so they do not need internet access or an API key.

## Project layout

| File | Purpose |
|---|---|
| `chatbot.py` | `chat()` function, shipment ID detection, system prompt, terminal loop |
| `database.py` | SQLite connection, table setup, shipment lookup |
| `knowledge_base.py` | Keyword search over the FAQ knowledge base |
| `llm_client.py` | Groq API call and conversion of Groq errors into friendly errors |
| `errors.py` | Custom error types, each with a user-friendly message |
| `config.py` | Settings (API key, model name, timeout, file paths) |
| `test_chatbot.py` | 21 unit tests |
| `data/` | Seed shipments and knowledge base |
