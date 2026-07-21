"""
ai_backend/main.py  –  LLM orchestration layer for GoodScore AI.

Two endpoints, both using ChatOpenAI (gpt-4o-mini):
  POST /chat        – Lean mode: pre-fetch context, single LLM call
  POST /agent-chat  – Agentic mode: tool-calling loop (ReAct-style)

NO Postgres imports. All data reaches the model via mock_api HTTP calls.
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from tools import ALL_TOOLS, _get_client, MOCK_API_URL

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_NAME = "gpt-4o-mini"

SYSTEM_PROMPT = """You are GoodScore AI, an expert financial and credit score advisor assistant.
You assist customers with their credit health, credit scores, bill payments, disputes, loan options, and account management.

You support 18 primary conversation flows:
1. score_analysis: Analyze current credit score, bureau breakdown, positive/negative factors.
2. score_improvement: Provide actionable advice to improve score based on customer factors.
3. score_trend: Show monthly score history trend over 12 months.
4. score_trend_summary: Summarize long-term score trajectory.
5. bill_payment: Fetch pending/overdue BBPS utility bills and execute payments.
6. dispute_closed_active: Check status of active and resolved credit report disputes.
7. dispute_fake: File a new dispute for incorrect, fraudulent, or fake accounts on credit report.
8. enquiry_removal: View credit enquiries (hard vs soft) and request removal of unauthorized hard pulls.
9. subscription_management: Check current GoodScore subscription plan and upgrade/downgrade plans.
10. financial_advice: Provide general guidance on financial planning, DTI ratio, and emergency funds.
11. report_update: Request a manual/expedited credit report update from bureaus.
12. loan_eligibility: Check personalized loan eligibility across lenders based on score.
13. loan_listing: Browse available personal, home, auto, education, and business loan offers.
14. contact_support: Create general customer support tickets for unresolved issues.
15. payment_security: Answer security queries, PCI-DSS compliance, 2FA, and BBPS protection.
16. bbps_refund: Request refund for failed or duplicate BBPS bill payments.
17. noc_mail_draft: Generate formal No Objection Certificate (NOC) draft letters for closed loans.
18. overdue_emi_conversion: Restructure or convert overdue EMIs to prevent credit score damage.

Be helpful, professional, precise, and clear. Use tools when needed to fetch real data or execute actions."""


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="GoodScore AI – Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    customer_id: str
    message: str
    conversation_history: list[dict] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _build_llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.3,
        streaming=True,
        **kwargs,
    )


async def _prefetch_context(customer_id: str) -> str:
    """Fetch customer profile, credit score, open tickets, and subscription in parallel for lean mode."""
    client = _get_client()
    cust_resp, score_resp, tickets_resp, sub_resp = await asyncio.gather(
        client.get(f"/customers/{customer_id}"),
        client.get(f"/customers/{customer_id}/credit-score"),
        client.get(f"/customers/{customer_id}/tickets"),
        client.get(f"/customers/{customer_id}/subscription"),
        return_exceptions=True
    )

    parts = []

    if not isinstance(cust_resp, Exception) and cust_resp.status_code == 200:
        c = cust_resp.json()
        parts.append(
            f"## Customer Profile\n"
            f"- ID: {c['customer_id']}\n- Name: {c['name']}\n"
            f"- Tier: {c['tier']}\n- Member since: {c['account_since']}\n"
            f"- Email: {c['email']}\n- PAN: {c.get('pan_masked', 'N/A')}"
        )
    else:
        parts.append(f"## Customer Profile\nCustomer {customer_id} not found.")

    if not isinstance(score_resp, Exception) and score_resp.status_code == 200:
        sdata = score_resp.json()
        s_lines = [f"- {s['bureau']}: {s['score']} ({s['checked_on']})" for s in sdata.get("latest_scores", [])]
        f_lines = [f"- [{f['impact'].upper()}] {f['factor']}: {f['detail']}" for f in sdata.get("score_factors", [])]
        parts.append(f"## Credit Scores\n" + "\n".join(s_lines) + "\n\n### Factors\n" + "\n".join(f_lines))

    if not isinstance(sub_resp, Exception) and sub_resp.status_code == 200:
        sub = sub_resp.json()
        parts.append(f"## Subscription\n- Plan: {sub.get('plan', 'free').upper()}\n- Status: {sub.get('status', 'active')}")

    if not isinstance(tickets_resp, Exception) and tickets_resp.status_code == 200:
        tickets = tickets_resp.json()
        if tickets:
            lines = ["## Open Tickets"]
            for t in tickets:
                esc = f" — escalated: {t['escalation_reason']}" if t.get("escalation_reason") else ""
                lines.append(f"- [{t['ticket_id']}] {t['subject']} (status={t['status']}, priority={t['priority']}){esc}")
            parts.append("\n".join(lines))

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# POST /chat  –  Lean pre-fetch pipeline
# ---------------------------------------------------------------------------
@app.post("/chat")
async def chat(req: ChatRequest):
    context = await _prefetch_context(req.customer_id)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=f"Here is the pre-fetched context for customer {req.customer_id}:\n\n{context}"),
    ]

    if req.conversation_history:
        for msg in req.conversation_history:
            role = msg.get("role", "user")
            if role == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    llm = _build_llm()

    async def generate():
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield f"data: {json.dumps({'content': chunk.content})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# POST /agent-chat  –  Agentic tool-calling pipeline
# ---------------------------------------------------------------------------
MAX_TOOL_ROUNDS = 10


@app.post("/agent-chat")
async def agent_chat(req: ChatRequest):
    llm = _build_llm().bind_tools(ALL_TOOLS)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(
            content=(
                f"You are assisting customer {req.customer_id}. "
                "Use the available tools to answer their queries or execute actions."
            ),
        ),
    ]

    if req.conversation_history:
        for msg in req.conversation_history:
            role = msg.get("role", "user")
            if role == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=req.message))

    tools_by_name = {t.name: t for t in ALL_TOOLS}

    async def generate():
        nonlocal messages

        for _round in range(MAX_TOOL_ROUNDS):
            response: AIMessage = await llm.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                if response.content:
                    yield f"data: {json.dumps({'content': response.content})}\n\n"
                break

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_fn = tools_by_name.get(tool_name)

                if tool_fn is None:
                    result = f"Error: unknown tool '{tool_name}'"
                else:
                    try:
                        result = await tool_fn.ainvoke(tool_args)
                    except Exception as e:
                        result = f"Error calling {tool_name}: {e}"

                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )

                yield f"data: {json.dumps({'tool_call': tool_name, 'args': tool_args, 'result_preview': str(result)[:200]})}\n\n"
        else:
            messages.append(
                HumanMessage(
                    content="Please summarize what you've found and respond to the user."
                )
            )
            final = await llm.ainvoke(messages)
            if final.content:
                yield f"data: {json.dumps({'content': final.content})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}
