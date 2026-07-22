# GoodScore AI — Financial & Credit Score Advisor Prototype

A multi-service AI financial assistant prototype powered by **GLM models** (`glm-4.5-air` / OpenAI-compatible API) via `langchain-openai`, backed by **Postgres**, supporting **18 specialized GoodScore conversation flows**, and orchestrated with **Docker Compose**.

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
| **OpenAI API Compatibility** | Seamlessly connects to GLM / Zhipu AI models (`glm-4.5-air`) using `langchain-openai` with custom `OPENAI_API_BASE`. |
| **Two LLM pipelines** | **Lean** (`/chat`): pre-fetches context, single LLM call. **Agentic** (`/agent-chat`): tool-calling loop, LLM decides what to fetch dynamically. |
| **18 Flow Domain Logic** | Handles credit score analysis, trends, BBPS bill payments, disputes, enquiry removals, subscriptions, loan eligibility, NOC drafting, and EMI conversions. |

---

## 18 Supported Conversation Flows

1. `score_analysis`: Analyze credit score breakdown across bureaus (CIBIL, Experian, Equifax) and key factors.
2. `score_improvement`: Actionable recommendations to improve credit scores.
3. `score_trend`: View 12-month historical score records.
4. `score_trend_summary`: Summarize long-term credit score trajectory.
5. `bill_payment`: Fetch and pay pending/overdue BBPS utility bills.
6. `dispute_closed_active`: Track status of open and resolved credit report disputes.
7. `dispute_fake`: File a new dispute for incorrect or fraudulent accounts.
8. `enquiry_removal`: View credit enquiries (hard vs soft) and request removal of unauthorized hard pulls.
9. `subscription_management`: View and upgrade/downgrade GoodScore plans (Free, Silver, Gold, Platinum).
10. `financial_advice`: Provide guidance on financial planning, emergency funds, and DTI ratios.
11. `report_update`: Request a manual/expedited credit report update from bureaus.
12. `loan_eligibility`: Check personalized loan eligibility across lenders.
13. `loan_listing`: Browse personal, home, auto, education, and business loan offers.
14. `contact_support`: Raise general support tickets for unresolved issues.
15. `payment_security`: Answer queries on PCI-DSS compliance, 2FA, and BBPS protection.
16. `bbps_refund`: Request refunds for failed or duplicate BBPS bill payments.
17. `noc_mail_draft`: Draft formal No Objection Certificate (NOC) letters for closed loans.
18. `overdue_emi_conversion`: Restructure or convert overdue EMIs into extended repayment plans.

---

## Quick Start (Docker Compose) 🐳

```bash
# 1. Clone the repository
git clone https://github.com/logaaparamesht-sys/good_score_agent.git
cd GoodScore_agent

# 2. Configure environment
cp .env.example .env
# Edit .env and configure your GLM / Zhipu API key & model settings:
#   OPENAI_API_KEY=your-api-key
#   OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4/
#   MODEL_NAME=glm-4.5-air

# 3. Launch the full stack
docker-compose up --build -d
```

Access the Streamlit Dashboard at [http://localhost:8501](http://localhost:8501).

### Data Persistence

| Command | Effect |
|---------|--------|
| `docker-compose down` | Stops services, **preserves data** (named volume `pgdata`) |
| `docker-compose up -d` | Restarts containers with existing data |
| `docker-compose down -v` | Stops services **and wipes data** — next `up` re-seeds from SQL |

---

## Local Dev (No Docker) 🔧

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
OPENAI_API_KEY=your-key OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4/ MODEL_NAME=glm-4.5-air MOCK_API_URL=http://localhost:8001 \
  uvicorn main:app --port 8000 --reload
```

### Terminal 3 — Dashboard
```bash
cd dashboard
pip install -r requirements.txt
AI_BACKEND_URL=http://localhost:8000 \
  streamlit run app.py --server.port 8501
```

---

## Project Structure

```
GoodScore_agent/
├── docker-compose.yml      # Full-stack orchestration
├── .env.example            # Environment variable template
├── README.md
├── db/
│   ├── schema.sql          # 9 table definitions (auto-applied on first boot)
│   └── seed.sql            # Rich synthetic dataset for 18 flows
├── mock_api/               # Data layer — ONLY service that touches Postgres
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── db.py               # asyncpg connection pool
│   └── main.py             # 15+ FastAPI endpoints
├── ai_backend/             # LLM layer — calls mock_api over HTTP, never DB
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tools.py            # 18 LangChain tools wrapping mock_api endpoints
│   └── main.py             # /chat (lean) + /agent-chat (agentic) endpoints
└── dashboard/              # UI layer — calls ai_backend over HTTP
    ├── Dockerfile
    ├── requirements.txt
    └── app.py              # Streamlit chat interface with sample prompts
```

---

## Technology Stack

- **LLM**: GLM models (`glm-4.5-air`) via `langchain-openai` (`ChatOpenAI` + custom API base)
- **API Layer**: FastAPI + Uvicorn (async)
- **Database**: PostgreSQL 16 + `asyncpg`
- **UI**: Streamlit
- **Orchestration**: Docker Compose
