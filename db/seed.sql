-- ============================================================
-- GoodScore Support AI  –  Seed Data
-- Runs automatically on first Postgres boot (after schema.sql)
--
-- 5 customers with diverse profiles, realistic Indian-market
-- credit data, bills, disputes, loans, subscriptions, etc.
-- ============================================================

-- ================================================================
-- CUSTOMERS
-- ================================================================
INSERT INTO customers (customer_id, name, tier, account_since, email, phone, pan_masked) VALUES
    ('C001', 'Alice Johnson',    'premium',    '2021-03-15', 'alice.johnson@example.com',  '+91-98765-43210', 'AXXPJ4521K'),
    ('C002', 'Bob Martinez',     'free',       '2022-07-01', 'bob.martinez@example.com',   '+91-87654-32109', 'BXXPM7832L'),
    ('C003', 'Carol Lee',        'enterprise', '2019-11-20', 'carol.lee@acmecorp.com',     '+91-76543-21098', 'CXXPL9123M'),
    ('C004', 'David Kim',        'standard',   '2023-01-10', 'david.kim@example.com',      '+91-65432-10987', 'DXXPK2345N'),
    ('C005', 'Eva Chen',         'gold',       '2020-06-05', 'eva.chen@example.com',       '+91-54321-09876', 'EXXPC6789P')
ON CONFLICT DO NOTHING;

-- ================================================================
-- TICKETS  (support history)
-- ================================================================
INSERT INTO tickets (ticket_id, customer_id, subject, status, priority, opened, escalation_reason) VALUES
    ('T1001', 'C001', 'Score dropped after credit card payment',     'open',      'high',   '2025-07-18', NULL),
    ('T1002', 'C001', 'BBPS refund not received',                    'open',      'medium', '2025-07-19', NULL),
    ('T1003', 'C002', 'Cannot view credit report',                   'open',      'high',   '2025-07-17', NULL),
    ('T1004', 'C003', 'Bulk employee score check request',           'open',      'low',    '2025-07-20', NULL),
    ('T1005', 'C003', 'Dispute filed but no update in 30 days',      'escalated', 'high',   '2025-07-15', 'Requires bureau liaison team review'),
    ('T1006', 'C004', 'Feature request: EMI calculator',             'open',      'low',    '2025-07-20', NULL),
    ('T1007', 'C005', 'NOC not received from lender after closure',  'open',      'medium', '2025-07-19', NULL)
ON CONFLICT DO NOTHING;

-- ================================================================
-- CREDIT SCORES  (latest per bureau per customer)
-- ================================================================
INSERT INTO credit_scores (customer_id, record_type, score, bureau, checked_on) VALUES
    ('C001', 'current', 762, 'CIBIL',    '2025-07-20'),
    ('C001', 'current', 748, 'Experian', '2025-07-18'),
    ('C001', 'current', 755, 'Equifax',  '2025-07-15'),
    ('C002', 'current', 623, 'CIBIL',    '2025-07-19'),
    ('C002', 'current', 610, 'Experian', '2025-07-10'),
    ('C003', 'current', 812, 'CIBIL',    '2025-07-20'),
    ('C003', 'current', 805, 'Experian', '2025-07-20'),
    ('C004', 'current', 580, 'CIBIL',    '2025-07-18'),
    ('C004', 'current', 572, 'Experian', '2025-07-12'),
    ('C005', 'current', 721, 'CIBIL',    '2025-07-20'),
    ('C005', 'current', 715, 'Experian', '2025-07-17')
ON CONFLICT DO NOTHING;

-- ================================================================
-- SCORE FACTORS  (what's helping / hurting each customer)
-- ================================================================
INSERT INTO credit_scores (customer_id, record_type, factor, impact, detail) VALUES
    -- Alice (762 – good)
    ('C001', 'factor', 'Payment History',       'positive', '98% on-time payments over 4 years — excellent track record'),
    ('C001', 'factor', 'Credit Utilization',    'negative', 'Using 68% of available credit limit; ideal is below 30%'),
    ('C001', 'factor', 'Credit Age',            'positive', 'Average account age is 6.2 years — long history helps'),
    ('C001', 'factor', 'Credit Mix',            'positive', 'Good mix: 2 credit cards, 1 home loan, 1 personal loan'),
    ('C001', 'factor', 'Recent Enquiries',      'negative', '3 hard enquiries in last 6 months — consider spacing applications'),

    -- Bob (623 – needs work)
    ('C002', 'factor', 'Payment History',       'negative', '4 late payments in the last 12 months — biggest drag on score'),
    ('C002', 'factor', 'Credit Utilization',    'negative', '82% utilization across 2 cards — heavily over-leveraged'),
    ('C002', 'factor', 'Credit Age',            'negative', 'Average account age only 1.8 years — too new'),
    ('C002', 'factor', 'Credit Mix',            'negative', 'Only credit cards, no installment loans — limited diversity'),
    ('C002', 'factor', 'Outstanding Debt',      'negative', 'Total outstanding: ₹3,45,000 across 2 accounts'),

    -- Carol (812 – excellent)
    ('C003', 'factor', 'Payment History',       'positive', '100% on-time payments over 6 years — flawless record'),
    ('C003', 'factor', 'Credit Utilization',    'positive', 'Only 12% utilization — well within ideal range'),
    ('C003', 'factor', 'Credit Age',            'positive', 'Average account age 8.5 years — very mature credit history'),
    ('C003', 'factor', 'Credit Mix',            'positive', 'Diverse: credit cards, home loan, car loan, business line of credit'),
    ('C003', 'factor', 'Recent Enquiries',      'positive', 'Only 1 soft enquiry in last 12 months'),

    -- David (580 – poor)
    ('C004', 'factor', 'Payment History',       'negative', '7 late payments including 2 defaults — severely impacting score'),
    ('C004', 'factor', 'Outstanding Debt',      'negative', 'Total outstanding: ₹8,20,000 with 2 accounts in collections'),
    ('C004', 'factor', 'Credit Utilization',    'negative', '95% utilization — nearly maxed out all credit lines'),
    ('C004', 'factor', 'Recent Enquiries',      'negative', '6 hard enquiries in last 3 months — signals credit-hungry behavior'),
    ('C004', 'factor', 'Credit Age',            'neutral',  'Average account age 2.5 years — moderate'),

    -- Eva (721 – good)
    ('C005', 'factor', 'Payment History',       'positive', '96% on-time payments — mostly reliable'),
    ('C005', 'factor', 'Credit Utilization',    'positive', '25% utilization — within healthy range'),
    ('C005', 'factor', 'Outstanding Debt',      'negative', '₹1,80,000 personal loan balance — moderate debt load'),
    ('C005', 'factor', 'Credit Mix',            'positive', 'Credit card + personal loan + gold loan — decent mix'),
    ('C005', 'factor', 'Credit Age',            'positive', 'Average account age 5 years')
ON CONFLICT DO NOTHING;

-- ================================================================
-- SCORE HISTORY  (monthly trend – 12 months per customer)
-- ================================================================
INSERT INTO credit_scores (customer_id, record_type, score, month, bureau) VALUES
    -- Alice – steady improvement
    ('C001', 'history', 710, '2024-08', 'CIBIL'), ('C001', 'history', 715, '2024-09', 'CIBIL'),
    ('C001', 'history', 718, '2024-10', 'CIBIL'), ('C001', 'history', 722, '2024-11', 'CIBIL'),
    ('C001', 'history', 730, '2024-12', 'CIBIL'), ('C001', 'history', 735, '2025-01', 'CIBIL'),
    ('C001', 'history', 738, '2025-02', 'CIBIL'), ('C001', 'history', 742, '2025-03', 'CIBIL'),
    ('C001', 'history', 748, '2025-04', 'CIBIL'), ('C001', 'history', 752, '2025-05', 'CIBIL'),
    ('C001', 'history', 758, '2025-06', 'CIBIL'), ('C001', 'history', 762, '2025-07', 'CIBIL'),

    -- Bob – declining trend
    ('C002', 'history', 698, '2024-08', 'CIBIL'), ('C002', 'history', 690, '2024-09', 'CIBIL'),
    ('C002', 'history', 682, '2024-10', 'CIBIL'), ('C002', 'history', 675, '2024-11', 'CIBIL'),
    ('C002', 'history', 668, '2024-12', 'CIBIL'), ('C002', 'history', 660, '2025-01', 'CIBIL'),
    ('C002', 'history', 652, '2025-02', 'CIBIL'), ('C002', 'history', 648, '2025-03', 'CIBIL'),
    ('C002', 'history', 641, '2025-04', 'CIBIL'), ('C002', 'history', 635, '2025-05', 'CIBIL'),
    ('C002', 'history', 629, '2025-06', 'CIBIL'), ('C002', 'history', 623, '2025-07', 'CIBIL'),

    -- Carol – consistently excellent
    ('C003', 'history', 798, '2024-08', 'CIBIL'), ('C003', 'history', 800, '2024-09', 'CIBIL'),
    ('C003', 'history', 802, '2024-10', 'CIBIL'), ('C003', 'history', 804, '2024-11', 'CIBIL'),
    ('C003', 'history', 805, '2024-12', 'CIBIL'), ('C003', 'history', 807, '2025-01', 'CIBIL'),
    ('C003', 'history', 808, '2025-02', 'CIBIL'), ('C003', 'history', 809, '2025-03', 'CIBIL'),
    ('C003', 'history', 810, '2025-04', 'CIBIL'), ('C003', 'history', 810, '2025-05', 'CIBIL'),
    ('C003', 'history', 811, '2025-06', 'CIBIL'), ('C003', 'history', 812, '2025-07', 'CIBIL'),

    -- David – volatile, dropping
    ('C004', 'history', 645, '2024-08', 'CIBIL'), ('C004', 'history', 638, '2024-09', 'CIBIL'),
    ('C004', 'history', 640, '2024-10', 'CIBIL'), ('C004', 'history', 625, '2024-11', 'CIBIL'),
    ('C004', 'history', 618, '2024-12', 'CIBIL'), ('C004', 'history', 610, '2025-01', 'CIBIL'),
    ('C004', 'history', 605, '2025-02', 'CIBIL'), ('C004', 'history', 598, '2025-03', 'CIBIL'),
    ('C004', 'history', 592, '2025-04', 'CIBIL'), ('C004', 'history', 588, '2025-05', 'CIBIL'),
    ('C004', 'history', 585, '2025-06', 'CIBIL'), ('C004', 'history', 580, '2025-07', 'CIBIL'),

    -- Eva – recovery arc
    ('C005', 'history', 680, '2024-08', 'CIBIL'), ('C005', 'history', 678, '2024-09', 'CIBIL'),
    ('C005', 'history', 682, '2024-10', 'CIBIL'), ('C005', 'history', 688, '2024-11', 'CIBIL'),
    ('C005', 'history', 692, '2024-12', 'CIBIL'), ('C005', 'history', 698, '2025-01', 'CIBIL'),
    ('C005', 'history', 702, '2025-02', 'CIBIL'), ('C005', 'history', 705, '2025-03', 'CIBIL'),
    ('C005', 'history', 710, '2025-04', 'CIBIL'), ('C005', 'history', 714, '2025-05', 'CIBIL'),
    ('C005', 'history', 718, '2025-06', 'CIBIL'), ('C005', 'history', 721, '2025-07', 'CIBIL')
ON CONFLICT DO NOTHING;

-- ================================================================
-- BILLS  (BBPS bill payments)
-- ================================================================
INSERT INTO bills (bill_id, customer_id, biller_name, category, amount, due_date, status, bbps_ref, paid_on) VALUES
    -- Alice
    ('B001', 'C001', 'Tata Power Mumbai',        'electricity', 2450.00, '2025-07-25', 'pending',  NULL, NULL),
    ('B002', 'C001', 'Jio Postpaid',             'mobile',      799.00,  '2025-07-20', 'paid',     'BBPS2507A001', '2025-07-18'),
    ('B003', 'C001', 'Airtel Xstream Fiber',     'broadband',   1499.00, '2025-07-28', 'pending',  NULL, NULL),
    ('B004', 'C001', 'LIC Premium',              'insurance',   12500.00,'2025-08-05', 'pending',  NULL, NULL),

    -- Bob
    ('B005', 'C002', 'BESCOM Bangalore',         'electricity', 1850.00, '2025-07-15', 'overdue',  NULL, NULL),
    ('B006', 'C002', 'Vi Postpaid',              'mobile',      599.00,  '2025-07-22', 'pending',  NULL, NULL),
    ('B007', 'C002', 'Mahanagar Gas',            'gas',         680.00,  '2025-07-10', 'paid',     'BBPS1007B002', '2025-07-10'),

    -- Carol
    ('B008', 'C003', 'Adani Electricity',        'electricity', 4200.00, '2025-07-30', 'pending',  NULL, NULL),
    ('B009', 'C003', 'Airtel Postpaid',          'mobile',      1299.00, '2025-07-18', 'paid',     'BBPS1807C001', '2025-07-17'),
    ('B010', 'C003', 'HDFC Ergo Health Insurance','insurance',  8900.00, '2025-08-01', 'pending',  NULL, NULL),
    ('B011', 'C003', 'ACT Fibernet',             'broadband',   1149.00, '2025-07-25', 'paid',     'BBPS2507C002', '2025-07-24'),

    -- David
    ('B012', 'C004', 'CESC Kolkata',             'electricity', 1650.00, '2025-07-12', 'overdue',  NULL, NULL),
    ('B013', 'C004', 'BSNL Landline',            'mobile',      450.00,  '2025-07-20', 'pending',  NULL, NULL),
    ('B014', 'C004', 'Indane Gas',               'gas',         920.00,  '2025-07-08', 'overdue',  NULL, NULL),

    -- Eva
    ('B015', 'C005', 'MSEDCL Maharashtra',       'electricity', 3100.00, '2025-07-26', 'pending',  NULL, NULL),
    ('B016', 'C005', 'Jio Postpaid',             'mobile',      999.00,  '2025-07-19', 'paid',     'BBPS1907E001', '2025-07-19'),
    ('B017', 'C005', 'Star Health Insurance',    'insurance',   6750.00, '2025-08-10', 'pending',  NULL, NULL),
    ('B018', 'C005', 'Hathway Broadband',        'broadband',   850.00,  '2025-07-22', 'refunded', 'BBPS2207E002', '2025-07-21')
ON CONFLICT DO NOTHING;

-- ================================================================
-- DISPUTES  (credit report disputes)
-- ================================================================
INSERT INTO disputes (dispute_id, customer_id, bureau, account_name, reason, status, filed_on, resolved_on) VALUES
    -- Alice – 1 resolved, 1 open
    ('D001', 'C001', 'CIBIL',    'HDFC Credit Card',       'incorrect_balance',  'resolved',    '2025-05-10', '2025-06-15'),
    ('D002', 'C001', 'Experian', 'Bajaj Finance Personal', 'paid_but_showing',   'in_progress', '2025-07-01', NULL),

    -- Bob – no disputes

    -- Carol – 1 resolved fraud case
    ('D003', 'C003', 'CIBIL',    'Unknown Personal Loan',  'not_my_account',     'resolved',    '2025-01-20', '2025-03-15'),
    ('D004', 'C003', 'CIBIL',    'Axis Bank Credit Card',  'duplicate',          'open',        '2025-07-10', NULL),

    -- David – active dispute
    ('D005', 'C004', 'CIBIL',    'Manappuram Gold Loan',   'incorrect_balance',  'open',        '2025-06-25', NULL),
    ('D006', 'C004', 'Experian', 'Home Credit Finance',    'not_my_account',     'open',        '2025-07-05', NULL),

    -- Eva – resolved
    ('D007', 'C005', 'CIBIL',    'ICICI Auto Loan',        'paid_but_showing',   'resolved',    '2025-04-01', '2025-05-20')
ON CONFLICT DO NOTHING;

-- ================================================================
-- ENQUIRIES  (hard/soft credit pulls)
-- ================================================================
INSERT INTO enquiries (enquiry_id, customer_id, lender, enquiry_type, enquiry_date, status) VALUES
    -- Alice – 3 hard, 1 soft
    ('E001', 'C001', 'HDFC Bank',         'hard', '2025-02-10', 'active'),
    ('E002', 'C001', 'ICICI Bank',        'hard', '2025-04-15', 'active'),
    ('E003', 'C001', 'Bajaj Finserv',     'hard', '2025-06-20', 'active'),
    ('E004', 'C001', 'CIBIL Self-Check',  'soft', '2025-07-20', 'active'),

    -- Bob – 2 hard
    ('E005', 'C002', 'Axis Bank',         'hard', '2025-05-01', 'active'),
    ('E006', 'C002', 'Kotak Mahindra',    'hard', '2025-06-10', 'active'),

    -- Carol – 1 soft only
    ('E007', 'C003', 'GoodScore Check',   'soft', '2025-07-15', 'active'),

    -- David – 6 hard (credit-hungry)
    ('E008', 'C004', 'SBI',               'hard', '2025-04-01', 'active'),
    ('E009', 'C004', 'PNB',               'hard', '2025-04-15', 'active'),
    ('E010', 'C004', 'HDFC Bank',         'hard', '2025-05-01', 'active'),
    ('E011', 'C004', 'Bajaj Finserv',     'hard', '2025-05-20', 'active'),
    ('E012', 'C004', 'Tata Capital',      'hard', '2025-06-05', 'active'),
    ('E013', 'C004', 'Home Credit',       'hard', '2025-06-25', 'active'),

    -- Eva – 2 hard, 1 removed
    ('E014', 'C005', 'ICICI Bank',        'hard', '2025-01-10', 'active'),
    ('E015', 'C005', 'Axis Bank',         'hard', '2025-03-22', 'active'),
    ('E016', 'C005', 'IndusInd Bank',     'hard', '2024-08-05', 'removed')
ON CONFLICT DO NOTHING;

-- ================================================================
-- SUBSCRIPTIONS  (GoodScore plan)
-- ================================================================
INSERT INTO subscriptions (sub_id, customer_id, plan, amount, billing_cycle, start_date, next_renewal, auto_renew, status) VALUES
    ('S001', 'C001', 'premium',  499.00,   'monthly',   '2024-01-15', '2025-08-15', TRUE,  'active'),
    ('S002', 'C002', 'free',     0.00,     'monthly',   '2022-07-01', NULL,          FALSE, 'active'),
    ('S003', 'C003', 'platinum', 4999.00,  'yearly',    '2024-11-20', '2025-11-20',  TRUE,  'active'),
    ('S004', 'C004', 'silver',   199.00,   'monthly',   '2024-06-10', '2025-08-10',  TRUE,  'active'),
    ('S005', 'C005', 'gold',     299.00,   'monthly',   '2023-06-05', '2025-08-05',  TRUE,  'active')
ON CONFLICT DO NOTHING;

-- ================================================================
-- LOANS  (marketplace / available offers)
-- ================================================================
INSERT INTO loans (loan_id, lender, loan_type, interest_rate, min_score, max_amount, tenure_months, processing_fee) VALUES
    -- Personal Loans
    ('L001', 'HDFC Bank',         'personal',  10.50, 700, 4000000.00,  60, '1% of loan amount'),
    ('L002', 'ICICI Bank',        'personal',  10.75, 680, 3500000.00,  60, '₹999 flat'),
    ('L003', 'Bajaj Finserv',     'personal',  11.00, 650, 2500000.00,  60, '1.5% of loan amount'),
    ('L004', 'Tata Capital',      'personal',  12.50, 600, 1500000.00,  48, '2% of loan amount'),
    ('L005', 'SBI',               'personal',  10.25, 720, 5000000.00,  72, '0.5% of loan amount'),

    -- Home Loans
    ('L006', 'SBI',               'home',       8.40, 700, 50000000.00, 360, '₹2,000 + GST'),
    ('L007', 'HDFC Ltd',          'home',       8.50, 680, 50000000.00, 360, '0.5% up to ₹10,000'),
    ('L008', 'ICICI Bank',        'home',       8.60, 700, 40000000.00, 300, '0.5% of loan amount'),
    ('L009', 'Kotak Mahindra',    'home',       8.70, 720, 35000000.00, 240, '₹5,000 flat'),

    -- Auto Loans
    ('L010', 'HDFC Bank',         'auto',       8.75, 650, 5000000.00,  84, '₹3,000 flat'),
    ('L011', 'Bank of Baroda',    'auto',       8.50, 680, 4000000.00,  84, '₹1,500 flat'),
    ('L012', 'Mahindra Finance',  'auto',       9.50, 600, 3000000.00,  72, '1% of loan amount'),

    -- Education Loans
    ('L013', 'SBI',               'education',  8.15, 650, 15000000.00, 180, 'Nil'),
    ('L014', 'Axis Bank',         'education',  9.00, 680, 10000000.00, 120, '₹5,000 flat'),

    -- Business Loans
    ('L015', 'HDFC Bank',         'business',  14.00, 720, 7500000.00,  60, '2% of loan amount'),
    ('L016', 'Lendingkart',       'business',  18.00, 600, 2000000.00,  36, '2-3% of loan amount')
ON CONFLICT DO NOTHING;

-- ================================================================
-- OVERDUE EMIs
-- ================================================================
INSERT INTO overdue_emis (emi_id, customer_id, loan_ref, lender, emi_amount, due_date, days_overdue, status, converted_to) VALUES
    -- Bob – 2 overdue
    ('EMI001', 'C002', 'HL-AX-2023-4521',  'Axis Bank',     18500.00,  '2025-06-05', 46,  'overdue',    NULL),
    ('EMI002', 'C002', 'PL-KM-2024-1122',  'Kotak Mahindra', 8750.00,  '2025-07-01', 20,  'overdue',    NULL),

    -- David – 3 overdue (serious delinquency)
    ('EMI003', 'C004', 'PL-SBI-2023-8890', 'SBI',            12200.00, '2025-05-10', 72,  'overdue',    NULL),
    ('EMI004', 'C004', 'GL-MAN-2024-3345', 'Manappuram',      5600.00, '2025-06-15', 36,  'overdue',    NULL),
    ('EMI005', 'C004', 'PL-HC-2024-5567',  'Home Credit',     7800.00, '2025-07-05', 16,  'overdue',    NULL),

    -- Eva – 1 already converted
    ('EMI006', 'C005', 'PL-ICICI-2023-7789','ICICI Bank',     9200.00, '2025-04-10', 0,   'converted',  'restructured')
ON CONFLICT DO NOTHING;

-- ================================================================
-- KNOWLEDGE BASE  (domain-specific articles for all 18 flows)
-- ================================================================
INSERT INTO kb_articles (kb_id, title, body) VALUES

    -- Score Analysis & Improvement
    ('KB001', 'Understanding Your Credit Score',
     'Your credit score (CIBIL score) ranges from 300 to 900. Here''s what the ranges mean:
• 300–549: Poor — Loan applications are likely to be rejected. Focus on clearing outstanding debts.
• 550–649: Below Average — Limited loan options with higher interest rates.
• 650–749: Good — Eligible for most loans at competitive rates.
• 750–799: Very Good — Access to premium loan offers and lowest interest rates.
• 800–900: Excellent — Best possible terms, pre-approved offers, and premium credit cards.

Your score is calculated based on: payment history (35%), credit utilization (30%), credit age (15%), credit mix (10%), and recent enquiries (10%).'),

    ('KB002', 'How to Improve Your Credit Score',
     'Follow these steps to improve your credit score:
1. **Pay bills on time**: Set up auto-pay or reminders. Even one missed payment can drop your score by 50-100 points.
2. **Reduce credit utilization**: Keep credit card usage below 30% of your limit. If your limit is ₹1,00,000, use no more than ₹30,000.
3. **Don''t close old accounts**: Length of credit history matters. Keep your oldest card active even if unused.
4. **Limit new credit applications**: Each hard enquiry drops your score by 5-10 points. Space applications at least 6 months apart.
5. **Diversify credit mix**: Having both revolving credit (cards) and installment loans (personal/home loan) helps.
6. **Check your report regularly**: Dispute any errors — incorrect information can silently drag your score down.
7. **Pay outstanding debts**: Settle or negotiate payment plans for accounts in collections.

Typical improvement timeline: 3-6 months for moderate improvements, 12-18 months for significant recovery from poor scores.'),

    -- Score Trends
    ('KB003', 'Reading Your Score Trend Report',
     'Your GoodScore dashboard tracks your credit score monthly across all three bureaus (CIBIL, Experian, Equifax). Key patterns to watch:
• **Upward trend**: Consistent improvement — your positive credit habits are working.
• **Downward trend**: Investigate — missed payments, increased utilization, or new hard enquiries may be the cause.
• **Flat trend**: Stable but stagnant — you may need to actively improve (reduce debt, diversify credit).
• **Volatile/zigzag**: Irregular behavior — could indicate inconsistent payments or fluctuating balances.

Tip: A score change of ±10 points month-over-month is normal fluctuation. Worry only about sustained trends over 3+ months.'),

    -- Bill Payment & BBPS
    ('KB004', 'BBPS Bill Payment Guide',
     'Bharat Bill Payment System (BBPS) is RBI''s authorized bill payment platform. Through GoodScore, you can pay:
• Electricity bills (all state & private DISCOMs)
• Mobile & DTH recharges (postpaid & prepaid)
• Broadband & landline bills
• Gas bills (piped & cylinder)
• Insurance premiums (life, health, motor)
• Municipal taxes & water bills

**Payment process**: Select biller → Enter consumer/account number → Verify amount → Pay via UPI/card/netbanking → Get BBPS receipt.

**Payment reflects**: Within 24-48 hours on your biller''s system. BBPS reference number is your proof of payment.

**Timely bill payments** are reported to credit bureaus and positively impact your credit score.'),

    ('KB005', 'BBPS Refund Process',
     'If a BBPS payment fails but money was debited, or if you were double-charged:
1. Note your BBPS reference number (starts with BBPS...).
2. Wait 48 hours — most failed transactions auto-reverse.
3. If not reversed, raise a refund request through GoodScore (Support → BBPS Refund).
4. Refunds are processed within 5-7 business days.
5. You''ll receive an SMS/email confirmation once the refund is credited.

**Escalation**: If the refund is not processed within 7 business days, the complaint is auto-escalated to the BBPS Central Unit (BCU). You can also file a complaint on the NPCI website using your BBPS reference number.'),

    -- Disputes
    ('KB006', 'How to Dispute Errors on Your Credit Report',
     'If you find incorrect information on your credit report, you can file a dispute:

**Common dispute reasons**:
• Incorrect outstanding balance
• Account marked delinquent despite payment
• Account that doesn''t belong to you (possible identity theft)
• Duplicate entries
• Wrong personal details (name, PAN, address)

**Process**:
1. Identify the error in your credit report on GoodScore.
2. File a dispute — select the bureau (CIBIL/Experian/Equifax) and the specific account.
3. Provide supporting documents (payment receipts, NOC, identity proof).
4. The bureau contacts the lender for verification (takes 15-30 days).
5. If validated, the bureau corrects your report and your score updates accordingly.

**Timeline**: CIBIL resolves most disputes within 30 days. Complex cases involving identity theft may take 45-60 days.'),

    ('KB007', 'Reporting Fraudulent Accounts',
     'If you find an account on your credit report that you never opened, it may be fraud:

**Immediate steps**:
1. File a dispute with the bureau marking it as "Not My Account."
2. File an FIR with your local police station.
3. Submit the FIR copy along with your identity documents (PAN, Aadhaar, passport).
4. Contact the lender directly and request an investigation.
5. Place a fraud alert on your credit file with all three bureaus.

**GoodScore helps by**:
• Monitoring your report for new accounts you didn''t open.
• Alerting you to hard enquiries you didn''t authorize.
• Premium members get identity theft insurance up to ₹1,00,000.

**Important**: You are NOT liable for loans taken fraudulently in your name, but you must report promptly. Delays weaken your case.'),

    -- Enquiry Removal
    ('KB008', 'Understanding and Removing Credit Enquiries',
     'Every time you apply for a loan or credit card, the lender does a "hard enquiry" on your credit report. This drops your score by 5-10 points.

**Hard vs Soft Enquiries**:
• **Hard**: Triggered by loan/credit applications. Visible to other lenders. Impacts score for 12-24 months.
• **Soft**: Self-checks, pre-approval checks, employer checks. Does NOT affect your score.

**Can you remove hard enquiries?**
• If you **did not authorize** the enquiry → File a dispute for unauthorized enquiry removal. Success rate: High (30-45 days).
• If you **authorized** it (applied for a loan) → Cannot be removed. It ages off automatically after 24 months.
• Multiple enquiries for the **same loan type within 14-45 days** are typically counted as one (rate shopping protection).

**Tip**: Before applying for loans, use GoodScore''s pre-qualification tool (soft enquiry only) to check eligibility without impacting your score.'),

    -- Subscription Management
    ('KB009', 'GoodScore Subscription Plans',
     'GoodScore offers four tiers:

| Plan | Price | Features |
|------|-------|----------|
| **Free** | ₹0 | Basic score (updated quarterly), limited report |
| **Silver** | ₹199/month | Monthly score updates, full report, basic alerts |
| **Gold** | ₹299/month | Weekly score updates, all 3 bureaus, score simulator, bill payments |
| **Platinum** | ₹4,999/year | Daily monitoring, identity theft insurance, dedicated advisor, loan offers, priority support |

**Subscription management**:
• Upgrade/downgrade anytime from Settings → Subscription.
• Changes take effect from the next billing cycle.
• Auto-renewal can be toggled on/off.
• Cancellation: Pro-rated refund for annual plans; no refund for monthly plans.
• Premium features are accessible immediately upon upgrade.'),

    -- Financial Advice
    ('KB010', 'General Financial Health Tips',
     'Building financial health alongside a good credit score:

**Emergency Fund**: Maintain 3-6 months of expenses in a liquid fund or savings account before taking on new debt.

**50/30/20 Rule**: Allocate 50% of income to needs, 30% to wants, 20% to savings/debt repayment.

**Debt-to-Income Ratio**: Keep total EMIs under 40% of monthly income. Lenders use this as a key eligibility metric.

**Insurance before Investment**: Ensure adequate term life (10x annual income) and health insurance (₹10-15 lakh family cover) before investing.

**SIP for Wealth Building**: Start systematic investment plans even with ₹500/month. Compounding over 10+ years creates significant wealth.

**Avoid**: Taking loans to fund lifestyle expenses, co-signing loans for others, using credit cards for cash advances (24-36% APR).'),

    -- Report Update
    ('KB011', 'How Credit Report Updates Work',
     'Your credit report updates when lenders submit data to bureaus. Here''s the typical cycle:

**Update frequency**: Most banks report to CIBIL monthly (by the 15th of each month for the previous month''s data).

**What triggers an update**: Loan payment, missed payment, new account opened, account closure, balance changes.

**Delay expectations**: A payment made on July 1 may reflect on your CIBIL report by August 20 (lender reports by Aug 15, bureau processes by Aug 20).

**Request a manual update**: If your report shows stale data:
1. Contact the lender with proof (payment receipt, closure letter, NOC).
2. Request them to update the bureau.
3. Follow up with the bureau directly if lender doesn''t respond in 15 days.
4. GoodScore Premium members can request expedited updates through our bureau liaison team.'),

    -- Loan Eligibility
    ('KB012', 'Loan Eligibility Criteria',
     'Your loan eligibility depends on multiple factors:

**Credit Score**: The minimum threshold varies by lender (typically 600-750). Higher scores unlock better rates and higher amounts.

**Income**: Salaried — minimum ₹25,000/month for personal loans. Self-employed — minimum ₹3,00,000 annual income.

**Debt-to-Income (DTI)**: Existing EMIs should not exceed 40-50% of monthly income.

**Employment stability**: Minimum 1 year with current employer (salaried) or 2 years of business vintage (self-employed).

**Age**: Typically 21-58 years (salaried), 25-65 years (self-employed).

**Documents needed**: PAN, Aadhaar, salary slips (3 months), bank statements (6 months), Form 16 / ITR.

**GoodScore Tip**: Use our loan eligibility calculator to check multiple lenders simultaneously with a single soft enquiry — no impact on your credit score.'),

    -- Payment Security
    ('KB013', 'Payment Security & Fraud Prevention',
     'GoodScore uses industry-leading security measures for all transactions:

**Payment Security**:
• All payments are processed through BBPS (RBI-regulated).
• 256-bit SSL encryption on all data transfers.
• Payments require OTP verification (2FA).
• No card/bank details are stored on our servers — processed via PCI-DSS certified payment gateways.

**Protecting yourself**:
• Never share your OTP, CVV, or login credentials with anyone — GoodScore will NEVER ask for these.
• Enable transaction alerts on your bank accounts.
• Use strong, unique passwords for your GoodScore account.
• Report suspicious activity immediately — call our fraud helpline or email security@goodscore.in.
• Check your credit report monthly for unauthorized accounts or enquiries.

**If you suspect fraud**: Lock your GoodScore account immediately from Settings → Security → Lock Account.'),

    -- NOC
    ('KB014', 'No Objection Certificate (NOC) Guide',
     'A No Objection Certificate (NOC) is issued by a lender after you fully repay a loan. It confirms that you have no outstanding dues.

**Why you need a NOC**:
• Required to remove the lien on property (home loans).
• Needed to transfer vehicle ownership (auto loans).
• Proof that the loan is closed — prevents future disputes on your credit report.

**How to get your NOC**:
1. After final payment, contact your lender and request the NOC.
2. Lender should issue NOC within 15-30 days of full repayment.
3. If delayed, send a formal letter/email citing RBI guidelines.
4. GoodScore can help draft this NOC request letter for you.

**What a NOC should contain**: Borrower name, loan account number, loan type, total amount, date of closure, and a clear statement that no dues are pending.

**RBI Guideline**: Banks must issue NOC and return original documents within 15 days of loan closure (RBI circular DBOD.No.Leg.BC.80/09.07.005/2013-14).'),

    -- Overdue EMI Conversion
    ('KB015', 'Overdue EMI Conversion Options',
     'If you have overdue EMIs, acting quickly can prevent further credit score damage. Options available:

**1. EMI Restructuring**:
Convert overdue EMIs into a new repayment schedule with extended tenure and potentially lower monthly payments. Lenders may charge a restructuring fee (1-2% of outstanding).

**2. Loan Settlement**:
Negotiate a one-time settlement for less than the full outstanding amount (typically 50-70%). Note: "Settled" status on your credit report is negative and stays for 7 years.

**3. EMI Holiday / Moratorium**:
Some lenders offer a temporary pause (1-3 months) on EMI payments. Interest continues to accrue during this period.

**4. Balance Transfer**:
Transfer the outstanding loan to another lender at a lower interest rate, resetting the repayment schedule.

**Impact on credit score**:
• Each day overdue causes incremental score damage.
• 30+ days: DPD (Days Past Due) reported to bureau — 50-80 point drop.
• 90+ days: Account flagged as NPA — 100-150 point drop.
• Act within 30 days to minimize damage.

**GoodScore recommendation**: Contact your lender immediately for restructuring. We can help initiate the conversation.'),

    -- Subscription / Account
    ('KB016', 'Managing Your GoodScore Account',
     'Account management options:
• **Change plan**: Settings → Subscription → Change Plan. Upgrades are instant; downgrades apply from next cycle.
• **Update email/phone**: Settings → Profile → Edit. Requires OTP verification.
• **Enable 2FA**: Settings → Security → Two-Factor Authentication.
• **Download reports**: Dashboard → Reports → Download PDF. Available in English and Hindi.
• **Delete account**: Settings → Account → Delete Account. This is irreversible — all data and history is permanently removed after 30 days.
• **Refer & Earn**: Share your referral code. Both you and your friend get 1 month of Gold plan free.')

ON CONFLICT DO NOTHING;

-- ================================================================
-- SPEND HISTORY  (Monthly spend category breakdown)
-- ================================================================
INSERT INTO spend_history (customer_id, month, category, amount) VALUES
    ('C001', '2025-07', 'utilities',      4748.00),
    ('C001', '2025-07', 'debt_repayment', 24500.00),
    ('C001', '2025-07', 'shopping',       18200.00),
    ('C001', '2025-07', 'dining',          6400.00),

    ('C002', '2025-07', 'utilities',      3129.00),
    ('C002', '2025-07', 'debt_repayment', 27250.00),
    ('C002', '2025-07', 'shopping',       12400.00),

    ('C003', '2025-07', 'utilities',      15448.00),
    ('C003', '2025-07', 'debt_repayment', 45000.00),
    ('C003', '2025-07', 'shopping',       32000.00),
    ('C003', '2025-07', 'travel',         19500.00),

    ('C004', '2025-07', 'utilities',      3020.00),
    ('C004', '2025-07', 'debt_repayment', 25600.00),
    ('C004', '2025-07', 'shopping',       14500.00),

    ('C005', '2025-07', 'utilities',      11699.00),
    ('C005', '2025-07', 'debt_repayment', 18400.00),
    ('C005', '2025-07', 'shopping',       21000.00)
ON CONFLICT DO NOTHING;
