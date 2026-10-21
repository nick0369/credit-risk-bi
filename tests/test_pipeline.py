import pandas as pd
import pytest

from credit_risk.pipeline import EXPECTED, build_marts, reconcile, summarize, validate


@pytest.fixture
def source():
    frame = pd.DataFrame([{column: 0 for column in EXPECTED} for _ in range(2)])
    frame['ID'] = [1, 2]
    frame['LIMIT_BAL'] = [100000, 200000]
    frame['AGE'] = [25, 40]
    frame['BILL_AMT1'] = [-100, 50000]
    frame['PAY_0'] = [0, 2]
    frame['default payment next month'] = [0, 1]
    return frame


def test_negative_bills_preserved_but_exposure_floored(source):
    accounts, months = build_marts(validate(source))
    assert accounts.positive_balance.tolist() == [0, 50000]
    assert months.bill_amount.sum() == 49900
    assert accounts.utilization.tolist() == [0, 0.25]


def test_duplicate_id_rejected(source):
    source['ID'] = 1
    with pytest.raises(ValueError, match='Duplicate'):
        validate(source)


@pytest.mark.parametrize('column,value', [('LIMIT_BAL', 0), ('AGE', 10),
                                         ('default payment next month', 3), ('PAY_0', 10),
                                         ('PAY_AMT1', -1), ('BILL_AMT1', None),
                                         ('ID', 1.5), ('LIMIT_BAL', float('inf'))])
def test_invalid_source_rejected(source, column, value):
    source[column] = source[column].astype(float)
    source.loc[0, column] = value
    with pytest.raises(ValueError):
        validate(source)


def test_reconciliation_detects_join_inflation(source):
    accounts, months = build_marts(source)
    assert all(c['passed'] for c in reconcile(source, accounts, months))
    inflated = pd.concat([accounts, accounts], ignore_index=True)
    assert not all(c['passed'] for c in reconcile(source, inflated, months))


def test_history_and_aggregate_grain(source):
    accounts, months = build_marts(source)
    summary = summarize(accounts, months)
    assert len(months) == 12
    assert months.statement_month.nunique() == 6
    assert sum(r['accounts'] for r in summary['segments']) == 2
    assert sum(r['defaults'] for r in summary['segments']) == 1


def test_missing_schema_rejected(source):
    with pytest.raises(ValueError, match='Missing columns'):
        validate(source.drop(columns=['ID']))
