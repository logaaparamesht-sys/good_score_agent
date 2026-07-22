-- ============================================================
-- GoodScore Support AI  –  Schema
-- Runs automatically on first Postgres boot via
-- /docker-entrypoint-initdb.d/
-- ============================================================

-- ---- Core ----

CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    name          TEXT        NOT NULL,
    tier          TEXT        NOT NULL DEFAULT 'standard',   -- free / standard / premium / enterprise
    account_since TEXT        NOT NULL,                      -- ISO-8601 date
    email         TEXT        NOT NULL,
    phone         TEXT,
    pan_masked    TEXT                                       -- e.g. AXXPX1234X
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id          TEXT PRIMARY KEY,
    customer_id        TEXT NOT NULL REFERENCES customers(customer_id),
    subject            TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'open',
    priority           TEXT NOT NULL DEFAULT 'medium',
    opened             TEXT NOT NULL,
    escalation_reason  TEXT
);

CREATE TABLE IF NOT EXISTS kb_articles (
    kb_id   TEXT PRIMARY KEY,
    title   TEXT NOT NULL,
    body    TEXT NOT NULL
);

-- ---- Credit Scores ----

CREATE TABLE IF NOT EXISTS credit_scores (
    id           SERIAL PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
    record_type  TEXT NOT NULL DEFAULT 'current',            -- current / factor / history
    score        INTEGER,                                    -- present for 'current' and 'history'
    bureau       TEXT DEFAULT 'CIBIL',                       -- CIBIL / Experian / Equifax
    checked_on   TEXT,                                       -- ISO-8601 date (for 'current')
    month        TEXT,                                       -- YYYY-MM (for 'history')
    factor       TEXT,                                       -- factor name (for 'factor')
    impact       TEXT,                                       -- positive / negative / neutral (for 'factor')
    detail       TEXT                                        -- factor description (for 'factor')
);

-- ---- Bills & Payments ----

CREATE TABLE IF NOT EXISTS bills (
    bill_id      TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
    biller_name  TEXT NOT NULL,
    category     TEXT NOT NULL,                              -- electricity / mobile / broadband / insurance / gas
    amount       NUMERIC(12,2) NOT NULL,
    due_date     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',            -- pending / paid / overdue / refunded
    bbps_ref     TEXT,
    paid_on      TEXT
);

-- ---- Disputes ----

CREATE TABLE IF NOT EXISTS disputes (
    dispute_id   TEXT PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
    bureau       TEXT NOT NULL DEFAULT 'CIBIL',
    account_name TEXT NOT NULL,
    reason       TEXT NOT NULL,                              -- incorrect_balance / not_my_account / paid_but_showing / duplicate / fraud
    status       TEXT NOT NULL DEFAULT 'open',               -- open / in_progress / resolved / rejected
    filed_on     TEXT NOT NULL,
    resolved_on  TEXT
);

-- ---- Enquiries ----

CREATE TABLE IF NOT EXISTS enquiries (
    enquiry_id    TEXT PRIMARY KEY,
    customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
    lender        TEXT NOT NULL,
    enquiry_type  TEXT NOT NULL DEFAULT 'hard',              -- hard / soft
    enquiry_date  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active'             -- active / removed
);

-- ---- Subscriptions ----

CREATE TABLE IF NOT EXISTS subscriptions (
    sub_id         TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customers(customer_id),
    plan           TEXT NOT NULL DEFAULT 'free',             -- free / silver / gold / platinum
    amount         NUMERIC(10,2) NOT NULL DEFAULT 0,
    billing_cycle  TEXT NOT NULL DEFAULT 'monthly',          -- monthly / quarterly / yearly
    start_date     TEXT NOT NULL,
    next_renewal   TEXT,
    auto_renew     BOOLEAN NOT NULL DEFAULT TRUE,
    status         TEXT NOT NULL DEFAULT 'active'            -- active / cancelled / expired
);

-- ---- Loans ----

CREATE TABLE IF NOT EXISTS loans (
    loan_id        TEXT PRIMARY KEY,
    lender         TEXT NOT NULL,
    loan_type      TEXT NOT NULL,                            -- personal / home / auto / education / business
    interest_rate  NUMERIC(5,2) NOT NULL,
    min_score      INTEGER NOT NULL,
    max_amount     NUMERIC(14,2) NOT NULL,
    tenure_months  INTEGER NOT NULL,
    processing_fee TEXT
);

-- ---- EMI / Overdue ----

CREATE TABLE IF NOT EXISTS overdue_emis (
    emi_id         TEXT PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customers(customer_id),
    loan_ref       TEXT NOT NULL,
    lender         TEXT NOT NULL,
    emi_amount     NUMERIC(12,2) NOT NULL,
    due_date       TEXT NOT NULL,
    days_overdue   INTEGER NOT NULL DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'overdue',          -- overdue / converted / paid
    converted_to   TEXT                                      -- NULL, 'restructured', 'extended'
);

-- ---- Spend History ----

CREATE TABLE IF NOT EXISTS spend_history (
    id           SERIAL PRIMARY KEY,
    customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
    month        TEXT NOT NULL,                              -- YYYY-MM
    category     TEXT NOT NULL,                              -- shopping / utilities / dining / travel / debt_repayment
    amount       NUMERIC(12,2) NOT NULL
);
