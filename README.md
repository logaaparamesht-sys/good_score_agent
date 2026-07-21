# Support AI — Customer Support Prototype

A multi-service AI customer-support prototype powered by **GPT-4o-mini**
(via `langchain-openai`), backed by **Postgres**, and orchestrated with
**Docker Compose**.

## Architecture

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐     ┌──────────┐
│   Dashboard  │────▶│  AI Backend   │────▶│   Mock API   │────▶│ Postgres │
│  (Streamlit) │     │  (LangChain)  │     │  (FastAPI)   │     │          │
│    :8501     │     │    :8000      │     │    :8001     │     │   :5432  │
└──────────────┘     └───────────────┘     └──────────────┘     └──────────┘
        UI                 LLM              Data Layer             Storage
```

### Key Design Decisions

| Principle | Implementation |
|-----------|---------------|
| **Model–DB separation** | `ai_backend` has zero Postgres imports. All data reaches the LLM exclusively through HTTP calls to `mock_api`. |
| **Two LLM pipelines** | **Lean** (`/chat`): pre-fetches context, single LLM call. **Agentic** (`/agent-chat`): tool-calling loop, LLM decides what to fetch. |
| **Swappable data layer** | Replace Postgres with a real CRM tomorrow — only `mock_api` changes. `ai_backend` and `dashboard` are untouched. |
| **Audit boundary** | Every piece of data the model sees is a logged HTTP call to `mock_api`. |

## Quick Start (Docker Compose) 🐳

```bash
# 1. Clone and enter the repo
git clone <your-repo-url>
cd GoodScore_agent

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key:
#   OPENAI_API_KEY=sk-...

# 3. Launch the full stack
docker-compose up --build
```

That's it. All four services start automatically:
- **Postgres** — schema + seed data applied on first boot
- **Mock API** — waits for Postgres to be healthy, then starts
- **AI Backend** — connects to Mock API
- **Dashboard** — opens at [http://localhost:8501](http://localhost:8501)

### Data Persistence

| Command | Effect |
|---------|--------|
| `docker-compose down` | Stops services, **preserves data** (named volume `pgdata`) |
| `docker-compose up` | Restarts with existing data |
| `docker-compose down -v` | Stops services **and wipes data** — next `up` re-seeds from SQL |

## Local Dev (No Docker) 🔧

For development, you can run services individually against a local Postgres instance.

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ running locally
- Create database and apply schema:
  ```bash
  psql -U support_user -d support_ai -f db/schema.sql
  psql -U support_user -d support_ai -f db/seed.sql
  ```

### Terminal 1 — Mock API
```bash
cd mock_api
pip install -r requirements.txt
DATABASE_URL=postgresql://support_user:support_pass@localhost:5432/support_ai \
  uvicorn main:app --port 8001 --reload
```

### Terminal 2 — AI Backend
```bash
cd ai_backend
pip install -r requirements.txt
OPENAI_API_KEY=sk-... MOCK_API_URL=http://localhost:8001 \
  uvicorn main:app --port 8000 --reload
```

### Terminal 3 — Dashboard
```bash
cd dashboard
pip install -r requirements.txt
AI_BACKEND_URL=http://localhost:8000 \
  streamlit run app.py --server.port 8501
```

## Project Structure

```
GoodScore_agent/
├── docker-compose.yml      # Full-stack orchestration
├── .env.example            # Environment variable template
├── README.md
├── db/
│   ├── schema.sql          # Table definitions (auto-applied on first boot)
│   └── seed.sql            # Fixture data (auto-applied on first boot)
├── mock_api/               # Data layer — ONLY service that touches Postgres
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── db.py               # asyncpg connection pool
│   └── main.py             # FastAPI endpoints
├── ai_backend/             # LLM layer — calls mock_api over HTTP, never DB
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tools.py            # LangChain tools wrapping mock_api endpoints
│   └── main.py             # /chat (lean) + /agent-chat (agentic) endpoints
└── dashboard/              # UI layer — calls ai_backend over HTTP
    ├── Dockerfile
    ├── requirements.txt
    └── app.py              # Streamlit chat interface
```

## API Endpoints

### Mock API (`:8001`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/customers/{id}` | Customer profile |
| `GET` | `/customers/{id}/tickets` | All tickets for a customer |
| `GET` | `/kb/search?query=...` | Search knowledge base |
| `POST` | `/tickets` | Create a new support ticket |
| `GET` | `/health` | Health check (includes DB connectivity) |

### AI Backend (`:8000`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Lean mode — pre-fetched context, single LLM call, SSE stream |
| `POST` | `/agent-chat` | Agentic mode — tool-calling loop, SSE stream |
| `GET` | `/health` | Health check |

Both endpoints accept:
```json
{
  "customer_id": "C001",
  "message": "What are my open tickets?",
  "conversation_history": []
}
```

## Technology Stack

- **LLM**: GPT-4o-mini via `langchain-openai` (`ChatOpenAI`)
- **API Layer**: FastAPI + Uvicorn (async)
- **Database**: PostgreSQL 16 + `asyncpg`
- **UI**: Streamlit
- **Orchestration**: Docker Compose
