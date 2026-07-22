"""
ai_backend/tools.py  –  LangChain tools that call mock_api over HTTP.

NO Postgres imports, connection strings, or ORM models here.
All data flows through mock_api's HTTP endpoints.
"""

import os
import httpx
from langchain_core.tools import tool

MOCK_API_URL = os.environ.get("MOCK_API_URL", "http://localhost:8001")

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=MOCK_API_URL, timeout=30.0)
    return _client


# ---------------------------------------------------------------------------
# Core Tools
# ---------------------------------------------------------------------------

@tool
async def get_customer_info(customer_id: str) -> str:
    """Look up a customer's profile by their customer ID (e.g. 'C001')."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}")
    if resp.status_code == 404:
        return f"No customer found with ID {customer_id}."
    resp.raise_for_status()
    data = resp.json()
    return (
        f"Customer {data['customer_id']}: {data['name']}, "
        f"tier={data['tier']}, member since {data['account_since']}, "
        f"email={data['email']}, phone={data.get('phone')}, PAN={data.get('pan_masked')}"
    )


@tool
async def get_open_tickets(customer_id: str) -> str:
    """Retrieve all support tickets for a customer."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/tickets")
    resp.raise_for_status()
    tickets = resp.json()
    if not tickets:
        return f"No tickets found for customer {customer_id}."
    lines = []
    for t in tickets:
        esc = f" (escalated: {t['escalation_reason']})" if t.get("escalation_reason") else ""
        lines.append(
            f"- [{t['ticket_id']}] {t['subject']} | "
            f"status={t['status']}, priority={t['priority']}, "
            f"opened={t['opened']}{esc}"
        )
    return "\n".join(lines)


@tool
async def create_support_ticket(customer_id: str, subject: str, priority: str = "medium") -> str:
    """Create a general support ticket for a customer."""
    client = _get_client()
    resp = await client.post(
        "/tickets",
        json={"customer_id": customer_id, "subject": subject, "priority": priority},
    )
    if resp.status_code == 404:
        return f"Cannot create ticket: customer {customer_id} not found."
    resp.raise_for_status()
    t = resp.json()
    return f"Ticket created successfully! ID={t['ticket_id']}, subject='{t['subject']}', priority={t['priority']}, status={t['status']}"


@tool
async def search_kb(query: str) -> str:
    """Search the knowledge base for articles matching a query string."""
    client = _get_client()
    resp = await client.get("/kb/search", params={"query": query})
    resp.raise_for_status()
    articles = resp.json()
    if not articles:
        return f"No knowledge-base articles found for '{query}'."
    parts = []
    for a in articles:
        parts.append(f"### {a['title']} ({a['kb_id']})\n{a['body']}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# GoodScore Flow-Specific Tools
# ---------------------------------------------------------------------------

@tool
async def get_credit_report(customer_id: str) -> str:
    """Fetch customer's full credit report (scores, factors, history, enquiryAccounts, recentEnquiryCount, accounts, disputes)."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/credit-report")
    if resp.status_code == 404:
        return f"No credit report found for customer {customer_id}."
    resp.raise_for_status()
    data = resp.json()
    scores = "\n".join([f"- {s['bureau']}: {s['score']} (as of {s['checked_on']})" for s in data.get("latest_scores", [])])
    factors = "\n".join([f"- [{f['impact'].upper()}] {f['factor']}: {f['detail']}" for f in data.get("score_factors", [])])
    enquiries = "\n".join([f"- [{e['enquiry_id']}] {e['lender']} ({e['enquiry_type']}) on {e['enquiry_date']}" for e in data.get("enquiryAccounts", [])])
    accounts = "\n".join([f"- [{a['account_id']}] {a['lender']} ({a['account_type']}) - Status: {a['status']}" for a in data.get("accounts", [])])
    disputes = "\n".join([f"- [{d['dispute_id']}] Bureau={d['bureau']} | Account={d['account_name']} | Status={d['status']}" for d in data.get("disputes", [])])
    
    return (
        f"### Credit Scores:\n{scores}\n\n"
        f"### Score Factors:\n{factors}\n\n"
        f"### Credit Enquiries (Recent hard enquiry count: {data.get('recentEnquiryCount', 0)}):\n{enquiries}\n\n"
        f"### User Accounts:\n{accounts}\n\n"
        f"### Disputes:\n{disputes}"
    )


@tool
async def get_credit_score(customer_id: str) -> str:
    """Fetch customer's credit score across bureaus (CIBIL, Experian, Equifax) and score factors."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/credit-score")
    if resp.status_code == 404:
        return f"No credit score data found for customer {customer_id}."
    resp.raise_for_status()
    data = resp.json()
    scores = "\n".join([f"- {s['bureau']}: {s['score']} (as of {s['checked_on']})" for s in data["latest_scores"]])
    factors = "\n".join([f"- [{f['impact'].upper()}] {f['factor']}: {f['detail']}" for f in data["score_factors"]])
    return f"### Credit Scores:\n{scores}\n\n### Score Factors:\n{factors}"


@tool
async def get_score_history(customer_id: str) -> str:
    """Fetch customer's 12-month credit score history and trend."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/score-history")
    resp.raise_for_status()
    history = resp.json()
    if not history:
        return f"No score history available for customer {customer_id}."
    lines = [f"- {h['month']}: {h['score']} ({h['bureau']})" for h in history]
    first, last = history[0]["score"], history[-1]["score"]
    diff = last - first
    trend_summary = f"Overall 12-month trend: {'up' if diff > 0 else 'down' if diff < 0 else 'stable'} by {abs(diff)} points (from {first} to {last})."
    return f"### Score History:\n" + "\n".join(lines) + f"\n\n{trend_summary}"


@tool
async def get_bills(customer_id: str) -> str:
    """Fetch customer's BBPS utility and service bills (billFetch data)."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/bills")
    resp.raise_for_status()
    bills = resp.json()
    if not bills:
        return f"No bills found for customer {customer_id}."
    lines = []
    for b in bills:
        ref = f" (Ref: {b['bbps_ref']})" if b.get("bbps_ref") else ""
        lines.append(f"- [{b['bill_id']}] {b['biller_name']} ({b['category']}): ₹{b['amount']} | due={b['due_date']} | status={b['status']}{ref}")
    return "### Customer Bills:\n" + "\n".join(lines)


@tool
async def pay_bill(customer_id: str, biller_name: str) -> str:
    """Pay a pending or overdue bill for a customer via BBPS."""
    client = _get_client()
    resp = await client.post(f"/customers/{customer_id}/bills/pay", json={"biller_name": biller_name})
    if resp.status_code == 400:
        return f"Failed to pay bill: {resp.json().get('detail')}"
    resp.raise_for_status()
    b = resp.json()
    return f"Bill payment successful! Paid ₹{b['amount']} to {b['biller_name']}. BBPS Ref: {b['bbps_ref']}."


@tool
async def request_bbps_refund(customer_id: str, bbps_ref: str, reason: str) -> str:
    """Request a refund for a failed or duplicate BBPS bill payment."""
    client = _get_client()
    resp = await client.post(f"/customers/{customer_id}/bills/refund", json={"bbps_ref": bbps_ref, "reason": reason})
    if resp.status_code == 404:
        return f"Refund request failed: {resp.json().get('detail')}"
    resp.raise_for_status()
    res = resp.json()
    return f"Refund request raised successfully! Ticket ID: {res['ticket_id']}. Message: {res['message']}"


@tool
async def get_disputes(customer_id: str) -> str:
    """Fetch customer's credit report disputes (both open/active and resolved)."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/disputes")
    resp.raise_for_status()
    disputes = resp.json()
    if not disputes:
        return f"No disputes found for customer {customer_id}."
    lines = []
    for d in disputes:
        res = f" (resolved on {d['resolved_on']})" if d.get("resolved_on") else ""
        lines.append(f"- [{d['dispute_id']}] Bureau={d['bureau']} | Account={d['account_name']} | Reason={d['reason']} | Status={d['status']} | Filed={d['filed_on']}{res}")
    return "### Disputes:\n" + "\n".join(lines)


@tool
async def file_dispute(customer_id: str, account_name: str, reason: str, bureau: str = "CIBIL") -> str:
    """File a new dispute for incorrect, duplicate, or fake accounts on credit report."""
    client = _get_client()
    resp = await client.post(
        f"/customers/{customer_id}/disputes",
        json={"bureau": bureau, "account_name": account_name, "reason": reason}
    )
    resp.raise_for_status()
    d = resp.json()
    return f"Dispute filed successfully! Dispute ID: {d['dispute_id']}, Bureau: {d['bureau']}, Account: {d['account_name']}, Status: {d['status']}."


@tool
async def get_enquiries(customer_id: str) -> str:
    """Fetch customer's credit enquiries (hard vs soft pulls)."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/enquiries")
    resp.raise_for_status()
    enquiries = resp.json()
    if not enquiries:
        return f"No credit enquiries recorded for customer {customer_id}."
    lines = [f"- [{e['enquiry_id']}] {e['lender']} | Type={e['enquiry_type']} | Date={e['enquiry_date']} | Status={e['status']}" for e in enquiries]
    return "### Credit Enquiries:\n" + "\n".join(lines)


@tool
async def request_enquiry_removal(customer_id: str, enquiry_id: str, reason: str) -> str:
    """Request removal of an unauthorized hard enquiry from credit report."""
    client = _get_client()
    resp = await client.post(
        f"/customers/{customer_id}/enquiries/removal",
        json={"enquiry_id": enquiry_id, "reason": reason}
    )
    if resp.status_code == 404:
        return f"Enquiry removal request failed: {resp.json().get('detail')}"
    resp.raise_for_status()
    res = resp.json()
    if res.get("status") == "info":
        return res["message"]
    return f"Enquiry removal request initiated! Ticket ID: {res['ticket_id']}. Message: {res['message']}"


@tool
async def get_subscription(customer_id: str) -> str:
    """Fetch customer's current GoodScore subscription plan details (subscriptionDetails)."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/subscription")
    resp.raise_for_status()
    s = resp.json()
    return f"Subscription Plan: {s['plan'].upper()} | Amount: ₹{s.get('amount', 0)} | Cycle: {s.get('billing_cycle', 'N/A')} | Auto-Renew: {s.get('auto_renew', False)} | Status: {s.get('status', 'active')}"


@tool
async def update_subscription(customer_id: str, plan: str, auto_renew: bool = True) -> str:
    """Upgrade or downgrade customer's GoodScore subscription plan (free, silver, gold, platinum)."""
    client = _get_client()
    resp = await client.put(
        f"/customers/{customer_id}/subscription",
        json={"plan": plan, "auto_renew": auto_renew}
    )
    resp.raise_for_status()
    s = resp.json()
    return f"Subscription updated! New Plan: {s['plan'].upper()}, Price: ₹{s['amount']}/month, Status: {s['status']}."


@tool
async def get_spend_history(customer_id: str) -> str:
    """Fetch customer's monthly spend history breakdown by category for financial advice."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/spend-history")
    resp.raise_for_status()
    data = resp.json()
    cats = "\n".join([f"- {c['category'].title()}: ₹{c['amount']}" for c in data.get("categories", [])])
    return f"### Spend History ({data.get('month', 'N/A')}):\nTotal Spend: ₹{data.get('total_spend', 0)}\n\nBreakdown:\n{cats}"


@tool
async def check_loan_eligibility(customer_id: str) -> str:
    """Check loan eligibility for a customer based on their credit score."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/loan-eligibility")
    resp.raise_for_status()
    data = resp.json()
    score = data["score"]
    loans = data["eligible_loans"]
    if not loans:
        return f"Based on credit score of {score}, customer {customer_id} is currently not eligible for loans requiring higher scores."
    lines = [f"- {l['lender']} {l['loan_type'].title()} Loan: Up to ₹{l['max_amount']} at {l['interest_rate']}% APR (Min Score: {l['min_score']})" for l in loans]
    return f"### Loan Eligibility (Score: {score}):\n" + "\n".join(lines)


@tool
async def get_available_loans() -> str:
    """Browse all available loan offers across lenders."""
    client = _get_client()
    resp = await client.get("/loans/available")
    resp.raise_for_status()
    loans = resp.json()
    lines = [f"- [{l['loan_id']}] {l['lender']} ({l['loan_type'].title()}): Up to ₹{l['max_amount']}, Rate: {l['interest_rate']}%, Min Score: {l['min_score']}" for l in loans]
    return "### Available Loans:\n" + "\n".join(lines)


@tool
async def request_report_update(customer_id: str) -> str:
    """Request a fresh/manual update of credit report from CIBIL/Experian."""
    client = _get_client()
    resp = await client.post(f"/customers/{customer_id}/report-update")
    resp.raise_for_status()
    res = resp.json()
    return f"Manual credit report update requested! Ticket ID: {res['ticket_id']}. {res['message']}"


@tool
async def draft_noc_letter(customer_id: str, lender: str, account_number: str) -> str:
    """Generate a formal No Objection Certificate (NOC) draft letter for loan closure."""
    client = _get_client()
    resp = await client.post(
        "/noc/draft",
        json={"customer_id": customer_id, "lender": lender, "account_number": account_number}
    )
    resp.raise_for_status()
    data = resp.json()
    return f"### Draft NOC Request Letter:\n```\n{data['draft_letter']}\n```"


@tool
async def get_overdue_eligibility(customer_id: str) -> str:
    """Fetch customer's overdue eligibility details and overdue EMI status."""
    client = _get_client()
    resp = await client.get(f"/customers/{customer_id}/overdue-eligibility")
    resp.raise_for_status()
    data = resp.json()
    emis = "\n".join([f"- [{e['emi_id']}] {e['lender']} ({e['loan_ref']}): ₹{e['emi_amount']} | {e['days_overdue']} days overdue | status={e['status']}" for e in data.get("overdue_emis", [])])
    return f"### Overdue EMI Eligibility:\nOverdue Count: {data.get('overdue_count', 0)}\nRestructuring Eligible: {data.get('eligible_for_restructuring', False)}\n\nOverdue EMIs:\n{emis}"


@tool
async def convert_overdue_emi(customer_id: str, emi_id: str, preferred_tenure: int = 12) -> str:
    """Convert/restructure an overdue EMI into a manageable repayment plan."""
    client = _get_client()
    resp = await client.post(
        f"/customers/{customer_id}/overdue-emi/convert",
        json={"emi_id": emi_id, "preferred_tenure": preferred_tenure}
    )
    if resp.status_code == 404:
        return f"EMI conversion failed: {resp.json().get('detail')}"
    resp.raise_for_status()
    res = resp.json()
    return f"EMI conversion initiated! Ticket ID: {res['ticket_id']}. {res['message']}"


@tool
async def route_to_freshchat_support(customer_id: str) -> str:
    """Route customer query to live Freshchat support queue (contact_support flow handler)."""
    client = _get_client()
    resp = await client.post(f"/customers/{customer_id}/contact-support")
    resp.raise_for_status()
    res = resp.json()
    return f"Freshchat Routing Complete: {res['message']} (Channel: {res['channel']}, Est. Wait: {res['estimated_wait_time']})"


# List of all tools for bind_tools
ALL_TOOLS = [
    get_customer_info,
    get_open_tickets,
    create_support_ticket,
    search_kb,
    get_credit_report,
    get_credit_score,
    get_score_history,
    get_bills,
    pay_bill,
    request_bbps_refund,
    get_disputes,
    file_dispute,
    get_enquiries,
    request_enquiry_removal,
    get_subscription,
    update_subscription,
    get_spend_history,
    check_loan_eligibility,
    get_available_loans,
    request_report_update,
    draft_noc_letter,
    get_overdue_eligibility,
    convert_overdue_emi,
    route_to_freshchat_support,
]
