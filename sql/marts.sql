CREATE OR REPLACE VIEW portfolio_segments AS
SELECT risk_segment, limit_band, COUNT(*) AS account_count,
       SUM(credit_limit) AS credit_limit_twd,
       SUM(positive_balance) AS positive_balance_twd,
       AVG(default_next_month::numeric) AS observed_default_rate,
       SUM(positive_balance) / NULLIF(SUM(credit_limit), 0) AS weighted_utilization,
       SUM(positive_balance) / NULLIF(SUM(SUM(positive_balance)) OVER (), 0) AS balance_share,
       DENSE_RANK() OVER (ORDER BY AVG(default_next_month::numeric) DESC) AS default_rate_rank
FROM accounts GROUP BY risk_segment, limit_band;

CREATE OR REPLACE VIEW repayment_trends AS
WITH monthly AS (
 SELECT statement_month, SUM(bill_amount) AS billed_twd,
        SUM(payment_amount) AS payments_twd,
        AVG(CASE WHEN repayment_status >= 1 THEN 1.0 ELSE 0 END) AS delayed_share
 FROM account_months GROUP BY statement_month
)
SELECT *, billed_twd - LAG(billed_twd) OVER (ORDER BY statement_month) AS bill_change_twd,
       AVG(payments_twd) OVER (ORDER BY statement_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
       AS three_month_avg_payments_twd
FROM monthly;

CREATE OR REPLACE VIEW account_repayment_change AS
SELECT account_id, statement_month, repayment_status,
       LAG(repayment_status) OVER (PARTITION BY account_id ORDER BY statement_month) AS previous_status,
       SUM(payment_amount) OVER (PARTITION BY account_id ORDER BY statement_month
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_payment_twd
FROM account_months;
