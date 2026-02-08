# Quick Start Guide - CPG Conversational AI (RelDB-Only)

**Get up and running in 5 minutes!**

> ⚠️ **Note**: This is the **RelDB-Only** version that uses DuckDB exclusively. For the version with ChromaDB vector database integration, see [Conv-AI-ChromaDB](https://github.com/varunmundas-de-stack/Conv-AI-ChromaDB).

## 1. Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check if pip works
pip --version

# Check if Ollama is installed (optional)
ollama --version
```

## 2. Install Dependencies

```bash
cd Conve-AI-Project-RelDB-Only
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed duckdb-1.4.4 ollama-0.1.0 pydantic-2.5.0 ...
```

## 3. Generate Sample Database

```bash
cd database
python generate_cpg_data.py
```

**Expected output:**
```
Creating CPG database at: database/cpg_olap.duckdb
Generating date dimension...
  Generated 90 date records
Generating product dimension...
  Generated 50 product records
...
Database created successfully!
```

**Result:** `cpg_olap.duckdb` file created with 1,000 sales records

## 4. Start the Web Interface

```bash
python frontend/app.py
```

**Expected output:**
```
============================================================
CPG Conversational AI Chatbot
============================================================
Starting Flask server...
Open your browser and go to: http://localhost:5000
Press Ctrl+C to stop the server
============================================================
 * Running on http://0.0.0.0:5000
```

## 5. Open Your Browser

Navigate to: **http://localhost:5000**

## 6. Try Sample Questions

Type any of these questions in the chat:

- "Show top 5 brands by sales value"
- "Weekly sales trend for last 6 weeks"
- "Total sales this month"
- "Sales by state"
- "Why did sales change?"
- "Compare sales by channel"

## Architecture Overview

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
┌──────▼──────────────────────────┐
│     Flask Web App (frontend/)   │
│  - Chat UI                      │
│  - API endpoints                │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Semantic Layer                │
│  - Intent parsing (Ollama)      │
│  - Query validation             │
│  - SQL generation               │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   DuckDB Query Executor         │
│  - Run SQL queries              │
│  - Return results               │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   DuckDB Database               │
│  - cpg_olap.duckdb              │
│  - Sales, products, geography   │
└─────────────────────────────────┘
```

## Key Components

- **Frontend**: Flask web app (`frontend/app.py`)
- **Database**: DuckDB relational database (`database/cpg_olap.duckdb`)
- **LLM**: Ollama for intent parsing (local)
- **Semantic Layer**: YAML-based business logic (`semantic_layer/config_cpg.yaml`)
- **Query Engine**: SQL generation and execution

## Troubleshooting

### Port 5000 Already in Use

```bash
# Find and kill the process
lsof -ti:5000 | xargs kill -9

# Or use a different port
python frontend/app.py --port 5001
```

### Ollama Not Responding

```bash
# Start Ollama
ollama serve

# Pull the model if needed
ollama pull mistral
```

### Database Not Found

```bash
# Regenerate the database
cd database
python generate_cpg_data.py
```

## Next Steps

- Read the [Testing Guide](TESTING_GUIDE.md) to verify your setup
- Review the [Architecture Document](ARCHITECTURE.md) to understand the system design
- Explore the semantic layer configuration in `semantic_layer/config_cpg.yaml`
- Check audit logs in `logs/audit.jsonl`

## What's Different from ChromaDB Version?

This **RelDB-Only** version:
- ✅ Uses only DuckDB (no vector database)
- ✅ Simpler architecture
- ✅ Faster setup (no embedding generation)
- ❌ No semantic search capabilities
- ❌ No AI-enhanced query mode
- ❌ No similar query suggestions

For semantic search and AI-enhanced features, see the [ChromaDB version](https://github.com/varunmundas-de-stack/Conv-AI-ChromaDB).
