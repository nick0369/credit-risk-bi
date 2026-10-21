"""Real PostgreSQL integration; skipped unless TEST_DATABASE_URL is explicitly set."""
import os
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from credit_risk.pipeline import EXPECTED, build_marts, load_database


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='PostgreSQL integration URL not configured')
def test_postgres_refresh_is_idempotent():
    source = pd.DataFrame([{c: 0 for c in EXPECTED}])
    source['ID'], source['LIMIT_BAL'], source['AGE'] = 1, 100000, 30
    accounts, months = build_marts(source)
    root = Path(__file__).resolve().parents[1]
    url = os.environ['TEST_DATABASE_URL']
    load_database(accounts, months, url, root)
    load_database(accounts, months, url, root)
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.execute(text('SELECT COUNT(*) FROM accounts')).scalar() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM account_months')).scalar() == 6
        assert connection.execute(text('SELECT COUNT(*) FROM repayment_trends')).scalar() == 6
        assert connection.execute(text('SELECT COUNT(*) FROM portfolio_segments')).scalar() == 1
    engine.dispose()
