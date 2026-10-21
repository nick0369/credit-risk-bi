# Data and KPI contracts

Source: Yeh, I. (2009). Default of Credit Card Clients. UCI. DOI https://doi.org/10.24432/C55S3H. CC BY 4.0. 30,000 Taiwanese accounts; April–September 2005 history and a next-month default outcome. Currency is New Taiwan dollars (TWD), not INR or USD.

## accounts: one row per original ID

| Field | Definition |
|---|---|
| account_id | Original dataset ID, unique within this extract |
| credit_limit | LIMIT_BAL; given credit including supplementary credit |
| latest_bill / latest_payment | BILL_AMT1 / PAY_AMT1, September source fields |
| positive_balance | max(latest_bill, 0), an exposure proxy rather than EAD |
| utilization | positive_balance / credit_limit; not capped at 100% |
| default_next_month | Source next-month binary outcome |
| risk_segment | PAY_0 >=2, PAY_0=1, or PAY_0<=0; descriptive only |
| limit_band | (0,100000], (100000,300000], (300000,infinity) TWD |

Age is retained for data validation but not used for risk segmentation. Sex, education and marriage are excluded from delivered marts. No decisions about real individuals are made.

## account_months: one row per (account_id, statement_month)

Six observations per account. BILL_AMT1..6 and PAY_AMT1..6 map September to April. Status mapping is PAY_0, PAY_2..6. Preserve negative bills and all original status codes. Nonpositive status codes are grouped without assigning undocumented semantics.

## KPI formulas

- Default rate = sum(default_next_month) / distinct accounts.
- Weighted utilization = sum(positive_balance) / sum(credit_limit). This differs from average account utilization.
- Exposure share = segment positive balance / portfolio positive balance.
- Scenario loss = positive balance * assumed PD * assumed LGD. It is not IFRS 9 ECL, a forecast, or realized losses.
- Payment and bill totals are independent monthly source fields. Do not treat their ratio as recovery or same-invoice repayment.

Joining accounts directly to monthly facts multiplies snapshot totals by six. Aggregate monthly data to account grain before combining totals. Use DAX measures on their own fact table.

The dataset supports neither current India risk estimates, investment portfolio returns, causal conclusions, realized profitability, nor monthly default-vintage curves.
