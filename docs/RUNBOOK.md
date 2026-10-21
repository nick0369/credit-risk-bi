# Operations and failure recovery

## Data flow

UCI ZIP → cached raw archive → validated XLS → accounts + account_months → reconciliation → CSV exports → optional PostgreSQL views → aggregate browser data.

`credit-risk build` is a full-refresh, single-writer batch. It is intentionally not an incremental production scheduler. Repeated builds produce the same business totals; timestamps change. Run builds serially.

Validation fails closed for missing columns, nulls, duplicates, invalid labels, nonpositive limits, underage records, invalid status codes or negative payments. Reconciliation must pass before CSV/database outputs are created. Negative bill balances remain valid.

PostgreSQL updates and view creation run in one transaction; database failure rolls back. CSV/dashboard files are local exports and are not in the database transaction. After a failure rerun the complete build and verify the output timestamp. A cached archive that fails to read must be moved aside before redownload. No silent synthetic fallback exists.

## Database access

Use a local demo password in your shell; production deployments need a secrets manager. Bind PostgreSQL to localhost. Use a separate read-only BI role with SELECT on accounts, account_months and reporting views. Never share the loader role with report consumers. Do not commit database URLs.

## Refresh checklist

1. Confirm source license/version and expected schema.
2. Run tests and the build; inspect exit status and JSON logs.
3. Review source SHA-256, nine reconciliation results and expected row counts.
4. Refresh BI and verify cards against validation.json.
5. Record genuine benchmarks before claiming time savings.

## Roadmap

Native Power BI report assembly; managed scheduler; credential rotation; alert delivery; multi-user access; object-storage artifacts. These are not claimed as implemented.
