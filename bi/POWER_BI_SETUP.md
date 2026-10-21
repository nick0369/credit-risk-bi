# Power BI Desktop handoff

A native `.pbix` is not included. The browser dashboard is working software; this document and `measures.dax` provide the native BI implementation steps.

1. Run the pipeline with PostgreSQL, or use Get Data > Text/CSV to import `data/processed/accounts.csv` and `account_months.csv`.
2. Set account IDs and outcomes to whole numbers, monetary fields to decimal numbers, statement_month to Date.
3. Relate accounts[account_id] (one) to account_months[account_id] (many), single direction. Disable automatic date relationships that create ambiguity.
4. Add each measure from `measures.dax` separately. Format default rate and utilization as percentages, amounts as TWD.
5. Overview: four KPI cards; segment/limit slicers; repayment segment default-rate bars; account detail matrix.
6. History: monthly bill and payment trends, with labels explaining that the outcome exists for one month only. Never plot repeated default labels as a trend.
7. Scenarios: add disconnected PD/LGD numeric parameters and scenario loss card. Label estimates hypothetical.
8. Use the report JSON as a QA checklist; reconcile unfiltered cards to `reports/validation.json`.
9. Desktop refresh uses local CSVs or database access. Service refresh may require an on-premises gateway and appropriate licensing.
10. Public sharing: only use sanitized public data. Publish to web exposes underlying data and is subject to tenant/license settings. Row-level security is not a public-sharing protection.

Palette: background #F3F6F7, navigation #102D35, teal #278783, text #182C38. Use 16:9 pages, consistent number formats, descriptive chart titles, and accessible contrast.
