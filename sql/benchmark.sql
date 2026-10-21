-- Run after loading. Save actual plans; no speedup is claimed in this project.
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM account_months WHERE account_id = 1000 ORDER BY statement_month;

-- Grain trap: joining the snapshot to six months multiplies account balances.
-- Correct: aggregate the history to one row per account before joining.
WITH history AS (
 SELECT account_id, SUM(payment_amount) AS payments FROM account_months GROUP BY account_id
)
SELECT SUM(a.credit_limit) AS limits, SUM(h.payments) AS historical_payments
FROM accounts a JOIN history h USING (account_id);
