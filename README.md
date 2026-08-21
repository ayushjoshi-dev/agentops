# AgentOps — AI-Powered Customer Operations Agent

> A production-grade Agentic AI application for e-commerce customer support.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange)](https://langchain-ai.github.io/langgraph)
[![Supabase](https://img.shields.io/badge/Database-Supabase_PostgreSQL-darkgreen)](https://supabase.com)
[![Render](https://img.shields.io/badge/Deployed_on-Render-purple)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🧠 Project Overview

AgentOps is an **Agentic AI Customer Operations Platform** for a fictional e-commerce company called **ShopEase**. Unlike a simple chatbot, AgentOps uses a **LangGraph multi-step agent** that:

1. **Reasons** about user intent
2. **Selects tools** (order lookup, product search, ticket creation, etc.)
3. **Executes tools** against a real database
4. **Retrieves knowledge** via RAG (Retrieval-Augmented Generation) from policy documents
5. **Generates grounded, cited answers** with full execution traceability

### Demo Query Flow
```
User: "My order ORD-1025 arrived damaged. Can I get a refund? Create a ticket."

Agent:
  1. → Calls get_order_details(order_id="ORD-1025")
  2. → Calls search_knowledge_base(query="refund policy damaged product")
  3. → Determines eligibility from order data + policy
  4. → Responds: "Yes, you're eligible for a full refund. Shall I create a ticket?"
  5. → Calls create_support_ticket(...)
  6. → Returns: Ticket TKT-0045 created. Trace: [2 tools, 1.8s, 2 sources]
```

---

## ✨ Features

- 🤖 **Multi-step AI Agent** powered by LangGraph with tool calling
- 📚 **RAG System** with pgvector semantic search over policy documents
- 🛠️ **7 Agent Tools**: order lookup, product search, ticket creation, calculator, and more
- 💬 **Conversational Memory** stored in PostgreSQL (not just in-memory)
- 🔍 **Agent Observability** — full execution trace with latency for every request
- 🔐 **JWT Authentication** — register, login, protected routes
- ⚠️ **Agent Safety** — confirmation required for destructive actions (cancel, refund)
- 📊 **AI Evaluation Framework** — 30 questions, tool accuracy, RAG hit rate metrics
- 🌐 **Channel-Independent Architecture** — ready for WhatsApp/Email adapters

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER BROWSER                         │
│            React + Vite Frontend (Render Static)        │
│   Chat UI | Agent Trace Panel | Conversation History    │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API (HTTPS)
┌─────────────────▼───────────────────────────────────────┐
│           FastAPI Backend (Render Web Service)          │
│  Auth | Chat | Orders | Tickets | Documents | Health    │
│                     │                                   │
│         ┌───────────▼──────────┐                       │
│         │    LangGraph Agent   │                       │
│         │  Agent → Tool → Loop │                       │
│         └───────────┬──────────┘                       │
│           ┌─────────┼──────────┐                       │
│       LLM (Groq)  Tools     RAG System                 │
│       llama-3.1   7 tools   pgvector search            │
└──────────────────┬──────────────────────────────────────┘
                   │ SQLAlchemy
┌──────────────────▼──────────────────────────────────────┐
│              Supabase PostgreSQL                        │
│  users | orders | products | tickets | conversations   │
│  messages | document_chunks (pgvector) | agent_runs    │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, Pydantic v2 |
| **Agent Orchestration** | LangGraph, LangChain |
| **LLM** | Groq (llama-3.1-8b-instant) — configurable |
| **Embeddings** | sentence-transformers (local, free) |
| **Vector Search** | PostgreSQL + pgvector |
| **Database** | Supabase PostgreSQL |
| **ORM** | SQLAlchemy + Alembic migrations |
| **Authentication** | JWT + bcrypt |
| **Frontend** | React + Vite |
| **Deployment** | Render (backend + frontend static) |
| **Version Control** | Git + GitHub (auto-deploy to Render) |
| **Testing** | Pytest + FastAPI TestClient |

---

## 🤖 Agent Tools

| Tool | Trigger Example | Description |
|------|----------------|-------------|
| `search_knowledge_base` | "What's your refund policy?" | Semantic search over policy docs |
| `get_order_status` | "Where is ORD-1025?" | Retrieve order status from DB |
| `get_order_details` | "Tell me about ORD-1025" | Full order info + items |
| `search_products` | "Find laptops under ₹60,000" | Product search with filters |
| `create_support_ticket` | "Create a ticket for my order" | Create DB ticket record |
| `get_customer_orders` | "Show my recent orders" | Customer order history |
| `calculate` | "10000 minus 10% restocking fee" | Safe math expressions |

---

## 📁 Project Structure

```
agentops/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/                 # Route handlers
│   │   ├── agents/              # LangGraph agent (graph, state, nodes)
│   │   ├── tools/               # Agent tools
│   │   ├── rag/                 # RAG pipeline (ingest, chunk, embed, retrieve)
│   │   ├── models/              # SQLAlchemy DB models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── channels/            # Channel adapters (web/whatsapp/email)
│   │   └── core/                # Config, DB, security, logging
│   ├── tests/
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # React + Vite
├── knowledge/                   # Policy documents for RAG
├── evaluation/                  # Eval dataset + script
├── render.yaml                  # Render deployment config
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/agentops.git
cd agentops
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase URL, Groq API key, JWT secret
```

### 3. Database setup
```bash
# Run Alembic migrations
alembic upgrade head

# Seed demo data
python -m app.scripts.seed_data
```

### 4. Ingest knowledge base
```bash
python -m app.rag.ingestion
```

### 5. Start backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Frontend setup
```bash
cd ../frontend
npm install
cp .env.example .env.local
# Set VITE_API_URL=http://localhost:8000
npm run dev
```

Visit: http://localhost:5173

API docs: http://localhost:8000/docs

---

## 🔑 Environment Variables

See [`backend/.env.example`](backend/.env.example) for all variables.

Key variables:
```env
DATABASE_URL=postgresql://...supabase.co:5432/postgres
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.1-8b-instant
JWT_SECRET=<64-char-random-hex>
CORS_ORIGINS=http://localhost:5173
```

---

## ☁️ Render Deployment

This project uses `render.yaml` for Infrastructure-as-Code deployment.

1. Push code to GitHub
2. Connect GitHub repo to Render
3. Set environment variables in Render dashboard
4. Every `git push main` triggers automatic redeploy

See [`render.yaml`](render.yaml) for full deployment configuration.

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

Test categories:
- `test_tools.py` — Unit tests for all agent tools
- `test_rag.py` — RAG retrieval accuracy
- `test_agent.py` — End-to-end agent behavior
- `test_api.py` — FastAPI integration tests

---

## 📊 AI Evaluation

```bash
cd evaluation
python evaluate.py
```

Metrics:
- Tool Selection Accuracy
- RAG Retrieval Hit Rate
- Citation Accuracy
- Average Response Latency
- Failure Rate

---

## 🔒 Security

- JWT authentication on all protected endpoints
- bcrypt password hashing
- Secrets via environment variables (never committed)
- Prompt injection defense in RAG system
- Agent safety: confirmation required for destructive actions

---

## 🗺️ Future Improvements

- WhatsApp integration via Meta Cloud API
- Email integration via SendGrid
- Redis caching for embeddings and frequent queries
- Streaming responses for real-time agent output
- LangSmith tracing integration
- Human-in-the-loop for complex cases

---

## 💼 Interview Discussion Points

See [`INTERVIEW_GUIDE.md`](INTERVIEW_GUIDE.md) for detailed answers to common AI Engineer interview questions about this project.

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

---

*Built as a portfolio project to demonstrate Agentic AI, RAG, LangGraph, and production Python backend skills.*
