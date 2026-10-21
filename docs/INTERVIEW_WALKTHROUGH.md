# Explain the project in an interview

## 60-second introduction

I built an independent credit portfolio analytics project using a public UCI dataset. I separated the account snapshot from six months of repayment history so joins would not inflate exposure. The Python pipeline validates source records, creates reporting marts and runs nine reconciliation checks. PostgreSQL views demonstrate ranking, lagged values and rolling aggregations. An interactive dashboard explains concentrations and includes an explicitly hypothetical loss calculator. I also supplied DAX and Power BI setup instructions.

## Be ready to demonstrate

1. Run the pipeline and explain the source fingerprint.
2. Show why an account-to-month join multiplies snapshot exposure by six.
3. Explain weighted utilization versus the average of account ratios.
4. Change filters and explain the denominator for default rate.
5. Set assumed PD to zero and show scenario loss becomes zero.
6. Explain why one future default label cannot form a monthly trend.
7. Show a failing duplicate-ID test and the integration-test design.
8. Explain what would be required before actual operational deployment.

## Honest résumé bullets

- Built a reproducible credit analytics pipeline covering 30,000 accounts and 180,000 monthly observations by validating public source data and separating account and history grains.
- Reconciled nine source-to-mart checks and tested malformed inputs and join inflation using pytest, supporting auditable dashboard reporting.
- Developed PostgreSQL window-function analyses and an interactive risk dashboard, identifying a 69.55% historical next-month default rate in the two-plus-month delayed segment.

Only claim PostgreSQL execution or successful CI once you have verified the corresponding run. Do not claim a native Power BI report until you assemble it in Desktop. Do not claim employment, realized savings or prevented defaults.
