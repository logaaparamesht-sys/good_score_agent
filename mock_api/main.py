"""
mock_api/main.py  –  FastAPI data-serving layer for GoodScore.

Reads from Postgres (via asyncpg); serves JSON to ai_backend.
If Postgres is unavailable, gracefully falls back to structured mock data.
"""

import asyncio
import random
import uuid
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from db import get_pool, close_pool


# ---------------------------------------------------------------------------
# Lifespan – warm up & tear down the DB pool
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()          # eagerly attempt pool creation at startup
    yield
    await close_pool()


app = FastAPI(title="GoodScore Support AI – Mock API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _jitter():
    """Small artificial latency so local dev resembles production timing."""
    await asyncio.sleep(random.uniform(0.02, 0.08))


def _row_to_dict(row) -> dict:
    """Convert an asyncpg Record to a plain dict, handling dates/numbers."""
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (date,)):
            d[k] = v.isoformat()
        elif hasattr(v, '__float__') and not isinstance(v, (int, float)):
            d[k] = float(v)
    return d


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class TicketCreate(BaseModel):
    customer_id: str
    subject: str
    priority: str = "medium"

class BillPayRequest(BaseModel):
    biller_name: str

class RefundRequest(BaseModel):
    bbps_ref: str
    reason: str

class DisputeCreate(BaseModel):
    bureau: str = "CIBIL"
    account_name: str
    reason: str

class EnquiryRemovalRequest(BaseModel):
    enquiry_id: str
    reason: str

class SubscriptionUpdate(BaseModel):
    plan: str
    auto_renew: bool = True

class NocDraftRequest(BaseModel):
    customer_id: str
    lender: str
    account_number: str

class EmiConversionRequest(BaseModel):
    emi_id: str
    preferred_tenure: int = 12


# ---------------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return {
            "customer_id": customer_id,
            "name": "Alice Johnson" if customer_id == "C001" else f"Customer {customer_id}",
            "tier": "premium",
            "account_since": "2021-03-15",
            "email": f"{customer_id.lower()}@example.com",
            "phone": "+91-98765-43210",
            "pan_masked": "AXXPJ4521K"
        }
    row = await pool.fetchrow("SELECT * FROM customers WHERE customer_id = $1", customer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _row_to_dict(row)


@app.get("/customers/{customer_id}/tickets")
async def get_customer_tickets(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {
                "ticket_id": "T1001",
                "customer_id": customer_id,
                "subject": "Score dropped after credit card payment",
                "status": "open",
                "priority": "high",
                "opened": "2025-07-18",
                "escalation_reason": None
            }
        ]
    rows = await pool.fetch("SELECT * FROM tickets WHERE customer_id = $1 ORDER BY opened DESC", customer_id)
    return [_row_to_dict(r) for r in rows]


@app.post("/tickets", status_code=201)
async def create_ticket(ticket: TicketCreate):
    await _jitter()
    pool = await get_pool()
    ticket_id = f"T{uuid.uuid4().hex[:6].upper()}"
    opened = date.today().isoformat()
    if pool is None:
        return {
            "ticket_id": ticket_id,
            "customer_id": ticket.customer_id,
            "subject": ticket.subject,
            "status": "open",
            "priority": ticket.priority,
            "opened": opened
        }
    cust = await pool.fetchrow("SELECT customer_id FROM customers WHERE customer_id = $1", ticket.customer_id)
    if cust is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    row = await pool.fetchrow(
        """
        INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened)
        VALUES ($1, $2, $3, 'open', $4, $5)
        RETURNING *
        """,
        ticket_id, ticket.customer_id, ticket.subject, ticket.priority, opened
    )
    return _row_to_dict(row)


@app.get("/kb/search")
async def search_kb(query: str = Query(..., min_length=1)):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {"kb_id": "KB01", "title": "Credit Score Calculation Factors", "body": "Payment history accounts for 35% of credit score."},
            {"kb_id": "KB02", "title": "BBPS Utility Bill Settlement", "body": "BBPS payments clear instantly or within 24 hours."}
        ]
    pattern = f"%{query}%"
    rows = await pool.fetch("SELECT * FROM kb_articles WHERE title ILIKE $1 OR body ILIKE $1", pattern)
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Credit Score & History Endpoints
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}/credit-score")
async def get_credit_score(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return {
            "latest_scores": [
                {"bureau": "CIBIL", "score": 762, "checked_on": "2025-07-20"},
                {"bureau": "Experian", "score": 748, "checked_on": "2025-07-18"},
                {"bureau": "Equifax", "score": 755, "checked_on": "2025-07-15"}
            ],
            "score_factors": [
                {"impact": "high", "factor": "On-time payment ratio", "detail": "99% on-time payment record across all active cards"},
                {"impact": "medium", "factor": "Credit Utilization", "detail": "18% limit utilization ratio"},
                {"impact": "low", "factor": "Recent Enquiries", "detail": "1 hard enquiry in the past 6 months"}
            ]
        }
    scores = await pool.fetch("SELECT * FROM credit_scores WHERE customer_id = $1 ORDER BY checked_on DESC", customer_id)
    factors = await pool.fetch("SELECT * FROM score_factors WHERE customer_id = $1", customer_id)
    if not scores:
        raise HTTPException(status_code=404, detail="No score found for customer")
    return {
        "latest_scores": [_row_to_dict(s) for s in scores],
        "score_factors": [_row_to_dict(f) for f in factors]
    }


@app.get("/customers/{customer_id}/score-history")
async def get_score_history(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {"month": "2024-08", "score": 730}, {"month": "2024-09", "score": 735},
            {"month": "2024-10", "score": 740}, {"month": "2024-11", "score": 742},
            {"month": "2024-12", "score": 745}, {"month": "2025-01", "score": 750},
            {"month": "2025-02", "score": 752}, {"month": "2025-03", "score": 755},
            {"month": "2025-04", "score": 758}, {"month": "2025-05", "score": 760},
            {"month": "2025-06", "score": 760}, {"month": "2025-07", "score": 762}
        ]
    rows = await pool.fetch("SELECT * FROM score_history WHERE customer_id = $1 ORDER BY month ASC", customer_id)
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Bills & Payments
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}/bills")
async def get_bills(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {"bill_id": "B101", "biller_name": "Tata Power", "amount": 1450.0, "status": "pending", "due_date": "2025-08-05"},
            {"bill_id": "B102", "biller_name": "Airtel Broadband", "amount": 999.0, "status": "overdue", "due_date": "2025-07-20"}
        ]
    rows = await pool.fetch("SELECT * FROM bills WHERE customer_id = $1 ORDER BY due_date ASC", customer_id)
    return [_row_to_dict(r) for r in rows]


@app.post("/customers/{customer_id}/bills/pay")
async def pay_bill(customer_id: str, req: BillPayRequest):
    await _jitter()
    pool = await get_pool()
    ref = f"BBPS{uuid.uuid4().hex[:8].upper()}"
    today = date.today().isoformat()
    if pool is None:
        return {
            "bill_id": "B101",
            "customer_id": customer_id,
            "biller_name": req.biller_name,
            "status": "paid",
            "bbps_ref": ref,
            "paid_on": today
        }
    row = await pool.fetchrow(
        """
        UPDATE bills SET status = 'paid', bbps_ref = $1, paid_on = $2
        WHERE customer_id = $3 AND biller_name = $4 AND status IN ('pending', 'overdue')
        RETURNING *
        """,
        ref, today, customer_id, req.biller_name
    )
    if not row:
        raise HTTPException(status_code=400, detail="No pending/overdue bill found for this biller")
    return _row_to_dict(row)


@app.post("/customers/{customer_id}/bills/refund")
async def request_bbps_refund(customer_id: str, req: RefundRequest):
    await _jitter()
    pool = await get_pool()
    ticket_id = f"T{uuid.uuid4().hex[:6].upper()}"
    if pool is None:
        return {
            "status": "refund_requested",
            "bbps_ref": req.bbps_ref,
            "ticket_id": ticket_id,
            "message": "Refund ticket raised. Resolution within 5-7 business days."
        }
    bill = await pool.fetchrow("SELECT * FROM bills WHERE customer_id = $1 AND bbps_ref = $2", customer_id, req.bbps_ref)
    if not bill:
        raise HTTPException(status_code=404, detail="No bill transaction found for the provided BBPS reference")
    opened = date.today().isoformat()
    await pool.execute(
        "INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened) VALUES ($1, $2, $3, 'open', 'high', $4)",
        ticket_id, customer_id, f"BBPS Refund Request for Ref {req.bbps_ref}: {req.reason}", opened
    )
    return {
        "status": "refund_requested",
        "bbps_ref": req.bbps_ref,
        "ticket_id": ticket_id,
        "message": "Refund ticket raised. Resolution within 5-7 business days."
    }


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}/disputes")
async def get_disputes(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {
                "dispute_id": "DSP101",
                "customer_id": customer_id,
                "bureau": "CIBIL",
                "account_name": "ABC Finance Personal Loan",
                "reason": "Account closed in 2023, still showing active",
                "status": "under_investigation",
                "filed_on": "2025-06-15"
            }
        ]
    rows = await pool.fetch("SELECT * FROM disputes WHERE customer_id = $1 ORDER BY filed_on DESC", customer_id)
    return [_row_to_dict(r) for r in rows]


@app.post("/customers/{customer_id}/disputes", status_code=201)
async def file_dispute(customer_id: str, req: DisputeCreate):
    await _jitter()
    pool = await get_pool()
    dispute_id = f"D{uuid.uuid4().hex[:5].upper()}"
    today = date.today().isoformat()
    if pool is None:
        return {
            "dispute_id": dispute_id,
            "customer_id": customer_id,
            "bureau": req.bureau,
            "account_name": req.account_name,
            "reason": req.reason,
            "status": "open",
            "filed_on": today
        }
    row = await pool.fetchrow(
        """
        INSERT INTO disputes (dispute_id, customer_id, bureau, account_name, reason, status, filed_on)
        VALUES ($1, $2, $3, $4, $5, 'open', $6)
        RETURNING *
        """,
        dispute_id, customer_id, req.bureau, req.account_name, req.reason, today
    )
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# Enquiries
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}/enquiries")
async def get_enquiries(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {"enquiry_id": "ENQ901", "customer_id": customer_id, "lender": "HDFC Bank", "enquiry_type": "hard", "enquiry_date": "2025-05-10"},
            {"enquiry_id": "ENQ902", "customer_id": customer_id, "lender": "SBI Card", "enquiry_type": "soft", "enquiry_date": "2025-06-01"}
        ]
    rows = await pool.fetch("SELECT * FROM enquiries WHERE customer_id = $1 ORDER BY enquiry_date DESC", customer_id)
    return [_row_to_dict(r) for r in rows]


@app.post("/customers/{customer_id}/enquiries/removal")
async def request_enquiry_removal(customer_id: str, req: EnquiryRemovalRequest):
    await _jitter()
    pool = await get_pool()
    ticket_id = f"T{uuid.uuid4().hex[:6].upper()}"
    if pool is None:
        return {
            "status": "dispute_initiated",
            "enquiry_id": req.enquiry_id,
            "ticket_id": ticket_id,
            "message": "Enquiry removal dispute submitted to bureau. Resolution in 30-45 days."
        }
    row = await pool.fetchrow("SELECT * FROM enquiries WHERE enquiry_id = $1 AND customer_id = $2", req.enquiry_id, customer_id)
    if not row:
        raise HTTPException(status_code=404, detail="Enquiry record not found")
    if row["enquiry_type"] == "soft":
        return {"status": "info", "message": "Soft enquiries do not affect your credit score and do not require removal."}
    opened = date.today().isoformat()
    await pool.execute(
        "INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened) VALUES ($1, $2, $3, 'open', 'medium', $4)",
        ticket_id, customer_id, f"Enquiry Removal Dispute for {req.enquiry_id} ({row['lender']}): {req.reason}", opened
    )
    return {
        "status": "dispute_initiated",
        "enquiry_id": req.enquiry_id,
        "ticket_id": ticket_id,
        "message": "Enquiry removal dispute submitted to bureau. Resolution in 30-45 days."
    }


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------
@app.get("/customers/{customer_id}/subscription")
async def get_subscription(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return {"plan": "gold", "amount": 299.0, "status": "active", "start_date": "2025-01-01"}
    row = await pool.fetchrow("SELECT * FROM subscriptions WHERE customer_id = $1 AND status = 'active'", customer_id)
    if not row:
        return {"plan": "free", "amount": 0.0, "status": "active"}
    return _row_to_dict(row)


@app.put("/customers/{customer_id}/subscription")
async def update_subscription(customer_id: str, req: SubscriptionUpdate):
    await _jitter()
    pool = await get_pool()
    plan_amounts = {"free": 0.0, "silver": 199.0, "gold": 299.0, "platinum": 4999.0}
    amount = plan_amounts.get(req.plan.lower(), 0.0)
    today = date.today().isoformat()
    sub_id = f"S{uuid.uuid4().hex[:5].upper()}"
    if pool is None:
        return {
            "sub_id": sub_id,
            "customer_id": customer_id,
            "plan": req.plan.lower(),
            "amount": amount,
            "status": "active",
            "start_date": today
        }
    await pool.execute("UPDATE subscriptions SET status = 'cancelled' WHERE customer_id = $1", customer_id)
    row = await pool.fetchrow(
        """
        INSERT INTO subscriptions (sub_id, customer_id, plan, amount, billing_cycle, start_date, auto_renew, status)
        VALUES ($1, $2, $3, $4, 'monthly', $5, $6, 'active')
        RETURNING *
        """,
        sub_id, customer_id, req.plan.lower(), amount, today, req.auto_renew
    )
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# Loans
# ---------------------------------------------------------------------------
@app.get("/loans/available")
async def get_available_loans():
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return [
            {"loan_id": "L101", "lender": "HDFC Bank", "loan_type": "Personal Loan", "min_score": 700, "max_amount": 500000.0, "interest_rate": 10.5},
            {"loan_id": "L102", "lender": "SBI", "loan_type": "Home Loan", "min_score": 750, "max_amount": 5000000.0, "interest_rate": 8.4}
        ]
    rows = await pool.fetch("SELECT * FROM loans ORDER BY interest_rate ASC")
    return [_row_to_dict(r) for r in rows]


@app.get("/customers/{customer_id}/loan-eligibility")
async def get_loan_eligibility(customer_id: str):
    await _jitter()
    pool = await get_pool()
    if pool is None:
        return {
            "customer_id": customer_id,
            "score": 762,
            "eligible_loans": [
                {"loan_id": "L101", "lender": "HDFC Bank", "loan_type": "Personal Loan", "min_score": 700, "max_amount": 500000.0, "interest_rate": 10.5},
                {"loan_id": "L102", "lender": "SBI", "loan_type": "Home Loan", "min_score": 750, "max_amount": 5000000.0, "interest_rate": 8.4}
            ]
        }
    score_row = await pool.fetchrow("SELECT score FROM credit_scores WHERE customer_id = $1 ORDER BY checked_on DESC LIMIT 1", customer_id)
    score = score_row["score"] if score_row else 600
    rows = await pool.fetch("SELECT * FROM loans WHERE min_score <= $1 ORDER BY interest_rate ASC", score)
    return {
        "customer_id": customer_id,
        "score": score,
        "eligible_loans": [_row_to_dict(r) for r in rows]
    }


# ---------------------------------------------------------------------------
# Report Update, NOC Draft, EMI Conversion
# ---------------------------------------------------------------------------
@app.post("/customers/{customer_id}/report-update")
async def request_report_update(customer_id: str):
    await _jitter()
    pool = await get_pool()
    ticket_id = f"T{uuid.uuid4().hex[:6].upper()}"
    if pool is None:
        return {
            "status": "update_requested",
            "ticket_id": ticket_id,
            "message": "Manual refresh request sent to CIBIL/Experian. Report will update within 24-48 hours."
        }
    opened = date.today().isoformat()
    await pool.execute(
        "INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened) VALUES ($1, $2, $3, 'open', 'medium', $4)",
        ticket_id, customer_id, "Manual Credit Report Refresh Request", opened
    )
    return {
        "status": "update_requested",
        "ticket_id": ticket_id,
        "message": "Manual refresh request sent to CIBIL/Experian. Report will update within 24-48 hours."
    }


@app.post("/noc/draft")
async def draft_noc_letter(req: NocDraftRequest):
    await _jitter()
    today = date.today().strftime("%B %d, %Y")
    draft = f"""Subject: Request for Issuance of No Objection Certificate (NOC) – Account No. {req.account_number}

Date: {today}

To,
The Loan Operations Manager,
{req.lender}

Dear Sir/Madam,

I am writing with reference to my loan account number {req.account_number} maintained with {req.lender}.

I have fully repaid all outstanding principal, interest, and associated charges towards the above-mentioned loan account. As per RBI guidelines, I request you to issue a formal No Objection Certificate (NOC) and close the loan account in your records and across all credit bureaus (CIBIL, Experian, Equifax).

Kindly dispatch the NOC to my registered address or send a soft copy to my email.

Thanking you,
Yours sincerely,
Customer ID: {req.customer_id}
"""
    return {"lender": req.lender, "account_number": req.account_number, "draft_letter": draft}


@app.post("/customers/{customer_id}/overdue-emi/convert")
async def convert_overdue_emi(customer_id: str, req: EmiConversionRequest):
    await _jitter()
    pool = await get_pool()
    ticket_id = f"T{uuid.uuid4().hex[:6].upper()}"
    if pool is None:
        return {
            "status": "converted",
            "emi_id": req.emi_id,
            "ticket_id": ticket_id,
            "new_tenure_months": req.preferred_tenure,
            "message": "Overdue EMI converted into restructured plan. Lender will reach out within 24 hours."
        }
    emi = await pool.fetchrow("SELECT * FROM overdue_emis WHERE emi_id = $1 AND customer_id = $2", req.emi_id, customer_id)
    if not emi:
        raise HTTPException(status_code=404, detail="Overdue EMI record not found")
    
    await pool.execute(
        "UPDATE overdue_emis SET status = 'converted', converted_to = 'restructured' WHERE emi_id = $1",
        req.emi_id
    )
    opened = date.today().isoformat()
    await pool.execute(
        "INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened) VALUES ($1, $2, $3, 'open', 'high', $4)",
        ticket_id, customer_id, f"EMI Restructuring Application for {emi['lender']} ({emi['loan_ref']})", opened
    )
    return {
        "status": "converted",
        "emi_id": req.emi_id,
        "ticket_id": ticket_id,
        "new_tenure_months": req.preferred_tenure,
        "message": f"Overdue EMI of ₹{float(emi['emi_amount'])} converted into restructured plan. Lender will reach out within 24 hours."
    }


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    pool = await get_pool()
    if pool is not None:
        try:
            await pool.fetchval("SELECT 1")
            return {"status": "ok", "db": "connected"}
        except Exception:
            pass
    return {"status": "ok", "db": "mock_fallback"}
