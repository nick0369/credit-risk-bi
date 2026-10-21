"""Validated ingestion, grain-safe marts, and auditable aggregate exports."""
from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect, text

LOGGER = logging.getLogger(__name__)
SOURCE = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
PAY_COLUMNS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
EXPECTED = (["ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLUMNS
            + [f"BILL_AMT{i}" for i in range(1, 7)] + [f"PAY_AMT{i}" for i in range(1, 7)]
            + ["default payment next month"])


def download(root: Path) -> Path:
    folder = root / "data/raw"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "uci-credit.zip"
    if not target.exists():
        temporary = target.with_suffix(".part")
        with urllib.request.urlopen(SOURCE, timeout=90) as response:
            temporary.write_bytes(response.read())
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError("Source archive checksum failure")
        temporary.replace(target)
    LOGGER.info(json.dumps({"event": "source_ready", "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}))
    return target


def read_source(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".xls")]
        if len(names) != 1:
            raise ValueError("Expected exactly one XLS workbook")
        with archive.open(names[0]) as workbook:
            return pd.read_excel(workbook, header=1, engine="xlrd")


def validate(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(EXPECTED) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    clean = frame[EXPECTED].copy()
    for column in EXPECTED:
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    if clean.empty or clean.isna().any().any():
        raise ValueError("Empty source or missing values")
    if not np.isfinite(clean.to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite numeric values")
    if not (clean.ID > 0).all() or not (clean.ID % 1 == 0).all():
        raise ValueError("Account IDs must be positive integers")
    if clean.ID.duplicated().any():
        raise ValueError("Duplicate account IDs")
    if not clean["default payment next month"].isin([0, 1]).all():
        raise ValueError("Default label must be binary")
    if (clean.LIMIT_BAL <= 0).any() or (clean.AGE < 18).any():
        raise ValueError("Invalid credit limit or age")
    if not clean[PAY_COLUMNS].isin(range(-2, 10)).all().all():
        raise ValueError("Unexpected repayment status code")
    if (clean[[f"PAY_AMT{i}" for i in range(1, 7)]] < 0).any().any():
        raise ValueError("Negative payment")
    # Negative bills are valid credit balances; preserve them in history.
    return clean


def build_marts(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    accounts = pd.DataFrame({
        "account_id": frame.ID.astype(int), "credit_limit": frame.LIMIT_BAL,
        "age": frame.AGE, "default_next_month": frame["default payment next month"].astype(int),
        "latest_bill": frame.BILL_AMT1, "latest_payment": frame.PAY_AMT1,
        "latest_status": frame.PAY_0,
    })
    accounts["positive_balance"] = accounts.latest_bill.clip(lower=0)
    accounts["utilization"] = accounts.positive_balance / accounts.credit_limit
    accounts["risk_segment"] = frame.PAY_0.map(
        lambda value: "2+ months delayed" if value >= 2 else "1 month delayed" if value == 1 else "No positive delay"
    )
    accounts["limit_band"] = pd.cut(
        frame.LIMIT_BAL, [0, 100000, 300000, float("inf")],
        labels=["Up to 100k", "100k–300k", "Above 300k"],
    ).astype(str)
    parts = []
    for i, status in enumerate(PAY_COLUMNS, 1):
        parts.append(pd.DataFrame({
            "account_id": frame.ID.astype(int), "statement_month": f"2005-{10-i:02d}-01",
            "bill_amount": frame[f"BILL_AMT{i}"], "payment_amount": frame[f"PAY_AMT{i}"],
            "repayment_status": frame[status],
        }))
    return accounts, pd.concat(parts, ignore_index=True)


def reconcile(source: pd.DataFrame, accounts: pd.DataFrame, months: pd.DataFrame) -> list[dict]:
    checks = {
        "account_count": len(source) == len(accounts),
        "unique_accounts": accounts.account_id.is_unique,
        "six_months_per_account": len(months) == 6 * len(source)
            and months.groupby("account_id").size().eq(6).all(),
        "unique_account_month": not months.duplicated(["account_id", "statement_month"]).any(),
        "credit_limit_total": abs(source.LIMIT_BAL.sum() - accounts.credit_limit.sum()) < 0.01,
        "latest_bill_total": abs(source.BILL_AMT1.sum() - accounts.latest_bill.sum()) < 0.01,
        "default_count": source["default payment next month"].sum() == accounts.default_next_month.sum(),
        "history_bill_total": abs(source[[f"BILL_AMT{i}" for i in range(1, 7)]].sum().sum()
                                  - months.bill_amount.sum()) < 0.01,
        "history_payment_total": abs(source[[f"PAY_AMT{i}" for i in range(1, 7)]].sum().sum()
                                     - months.payment_amount.sum()) < 0.01,
    }
    return [{"check": name, "passed": bool(passed)} for name, passed in checks.items()]


def summarize(accounts: pd.DataFrame, months: pd.DataFrame) -> dict:
    segments = []
    for (risk, band), group in accounts.groupby(["risk_segment", "limit_band"], observed=True):
        segments.append({"risk": risk, "band": band, "accounts": len(group),
                         "defaults": int(group.default_next_month.sum()),
                         "limits": float(group.credit_limit.sum()),
                         "balance": float(group.positive_balance.sum()),
                         "bill": float(group.latest_bill.sum()),
                         "payment": float(group.latest_payment.sum())})
    history = months.groupby("statement_month", as_index=False).agg(
        bill=("bill_amount", "sum"), payment=("payment_amount", "sum"),
        delayed=("repayment_status", lambda s: int((s >= 1).sum())), accounts=("account_id", "count"))
    return {"segments": segments, "history": history.to_dict("records")}


def load_database(accounts: pd.DataFrame, months: pd.DataFrame, url: str, root: Path) -> None:
    engine = create_engine(url)
    # One transaction: a failed model build restores the previous working tables.
    with engine.begin() as connection:
        for name, frame in [("account_months", months), ("accounts", accounts)]:
            if inspect(connection).has_table(name):
                connection.execute(text(f"DELETE FROM {name}"))
            frame.to_sql(name, connection, if_exists="append", index=False, chunksize=1000)
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS accounts_pk ON accounts(account_id)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS months_pk ON account_months(account_id, statement_month)"))
        for statement in (root / "sql/marts.sql").read_text(encoding="utf-8").split(";"):
            if statement.strip():
                connection.execute(text(statement))
    engine.dispose()


def run(root: Path, database_url: str | None = None) -> dict:
    archive = download(root)
    source = validate(read_source(archive))
    accounts, months = build_marts(source)
    checks = reconcile(source, accounts, months)
    if not all(check["passed"] for check in checks):
        raise ValueError(f"Reconciliation failure: {checks}")
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    accounts.to_csv(processed / "accounts.csv", index=False)
    months.to_csv(processed / "account_months.csv", index=False)
    if database_url:
        load_database(accounts, months, database_url, root)
    report = {"source": SOURCE, "source_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "built_at_utc": datetime.now(UTC).isoformat(), "currency": "TWD",
              "accounts": len(accounts), "account_months": len(months), "checks": checks,
              "default_rate": float(accounts.default_next_month.mean()),
              "positive_balance": float(accounts.positive_balance.sum()),
              "credit_limits": float(accounts.credit_limit.sum()),
              "database_loaded": bool(database_url)}
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports/validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    payload = {**summarize(accounts, months), "validation": report}
    (root / "dashboard/data.js").write_text("window.PORTFOLIO = " + json.dumps(payload) + ";", encoding="utf-8")
    LOGGER.info(json.dumps({"event": "pipeline_complete", **report}))
    return report
