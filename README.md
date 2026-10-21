# CreditScope — Executive Credit Risk & Portfolio Dashboard

An independent Data Analyst portfolio project that turns a historical credit-card extract into reconciled reporting marts, advanced SQL analyses, and an interactive dashboard.

**30,000 accounts · 180,000 monthly observations · 9 reconciliation checks · TWD currency**

![Dashboard preview](dashboard/preview.png)

## Business question

Which repayment segments concentrate observed default risk and billed exposure, and what should a risk manager investigate next?

The deliverable supports portfolio review and reporting assurance. It does not approve loans, forecast investment returns, or establish real-world savings.

## View the dashboard

Open `dashboard/index.html` directly in a browser; the included `data.js` contains derived aggregate data only. Filters, loss-scenario sliders and CSV export work without a backend or API key.

Alternatively:

```sh
python -m http.server 8765 --directory dashboard
```

Then visit http://localhost:8765. For GitHub Pages, select **Settings → Pages → Source: GitHub Actions**, then run **Publish browser dashboard** from Actions. A live URL is not claimed until deployment succeeds.

## Architecture

```mermaid
flowchart LR
    A[UCI XLS archive] --> B[Validated Python ingestion]
    B --> C[Account snapshot]
    B --> D[Account-month history]
    C --> E[Reconciliation gates]
    D --> E
    E --> F[PostgreSQL tables and SQL views]
    E --> G[CSV exports]
    E --> H[Aggregate browser dashboard]
    F --> I[Power BI Desktop handoff]
    G --> I
```

## Reproduce the real-data pipeline

Python 3.11+ recommended; tested locally with Python 3.12. Internet is required for the first UCI download.

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
credit-risk build
pytest -q
ruff check .
```

Run from the repository root. For an environment matching this build, install `requirements-lock.txt` before the editable install. It lists the locally resolved versions; the package manifest declares supported ranges.

Outputs: ignored raw archive, ignored account-level CSV files, `reports/validation.json`, and `dashboard/data.js`. Source SHA-256 is recorded. The browser export contains no account IDs.

## PostgreSQL mode

Docker is optional for the browser/CSV build and required for the Compose path below.

PowerShell:

```powershell
$env:POSTGRES_PASSWORD = 'choose_a_local_demo_password'
docker compose up -d --wait
$env:DATABASE_URL = 'postgresql+psycopg://credit:choose_a_local_demo_password@localhost:5432/credit'
credit-risk build
```

Use a URL-safe password or percent-encode special characters in the database URL. The loader performs a transactional full refresh, preserves reporting views on rerun, and creates unique indexes. Use a dedicated test database when setting `TEST_DATABASE_URL`: the integration test replaces project table contents there.

SQL deliverables:

- `portfolio_segments`: weighted utilization, balance concentration and `DENSE_RANK`.
- `repayment_trends`: `LAG` and a three-month rolling payment average.
- `account_repayment_change`: partitioned status history and cumulative payments.
- `sql/benchmark.sql`: reproducible `EXPLAIN (ANALYZE, BUFFERS)` and a grain-safe join example.

No database query speedup is claimed without an actual benchmark.

## Power BI handoff

Follow [bi/POWER_BI_SETUP.md](bi/POWER_BI_SETUP.md) and add the measures from [bi/measures.dax](bi/measures.dax). Connect to PostgreSQL or generated CSVs. No native `.pbix` or `.pbit` is included, and no Power BI Desktop execution is claimed.

## Measured source findings

- Next-month default rate: **22.12%** across 30,000 accounts.
- Positive September billed balance: **TWD 1,537,381,257**.
- Credit limits: **TWD 5,024,529,680**; weighted utilization: **30.60%**.
- Accounts with September status of two or more months delayed: **3,130 accounts**, with **69.55%** observed next-month default versus **13.83%** in the no-positive-delay group.

Recommendation: prioritize investigation of the delayed segment's exposure and repayment patterns; assess policy changes only after out-of-time validation and appropriate review. These are associations in a historical dataset, not causal intervention effects.

## Business value and ROI

This project makes metric definitions and reconciliation auditable and offers repeatable reporting. Track reporting preparation time before/after automation to quantify actual efficiency.

Illustrative scenario only: saving 105 minutes per weekly report gives 91 hours annually. This has not been measured here and must not be presented as delivered savings.

The dashboard's loss calculator uses positive billed balance × assumed PD × assumed LGD. It is a transparent scenario, not calibrated expected loss or IFRS 9 ECL.

## Quality and verification

- 13 local unit tests passed; malformed inputs, negative bill handling, grain inflation and source totals are covered.
- All 9 real-data reconciliation checks passed.
- Local lint passed.
- Browser filters, zero-PD scenario, and reset were exercised.
- PostgreSQL integration is configured in CI using a PostgreSQL 16 service; it was skipped locally because a local server was unavailable. Check the Actions run for its actual status.

## Repository map

```text
src/credit_risk/       ingestion, validation, marts, loader and CLI
sql/                  PostgreSQL reporting views and query analysis
dashboard/            standalone interactive dashboard + aggregate data
bi/                   Power BI build instructions and DAX measures
tests/                unit tests and opt-in PostgreSQL integration test
reports/              real-data reconciliation and source fingerprint
docs/                 definitions, operations and interview walkthrough
.github/workflows/    CI and optional Pages publication
```

## Limitations and attribution

Source: Yeh, I. (2009), *Default of Credit Card Clients*, UCI Machine Learning Repository, [DOI: 10.24432/C55S3H](https://doi.org/10.24432/C55S3H), CC BY 4.0. Transformations: unpivoted history, derived balance/segment metrics, and aggregate exports. Code uses the MIT license; source and derived data retain attribution requirements.

This is an old Taiwanese portfolio with April–September 2005 history and one subsequent outcome. Do not generalize results to today's Indian lending or payments systems. Negative bills are preserved in history; exposure proxies floor them at zero. No employer affiliation, paid work experience, model deployment, or production use is implied.

See [data contracts](docs/DATA_DICTIONARY.md) and [runbook](docs/RUNBOOK.md).
