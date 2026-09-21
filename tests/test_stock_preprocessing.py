import pandas as pd

from stocks.preprocessing import daily_to_weekly


def make_trading_days(start: str, periods: int) -> pd.DataFrame:
    idx = pd.bdate_range(start, periods=periods, tz="UTC")
    base = pd.Series(range(1, periods + 1), index=idx, dtype=float)

    return pd.DataFrame(
        {
            "Open": base,
            "High": base + 1,
            "Low": base - 1,
            "Close": base + 0.5,
            "Volume": 10.0,
        },
        index=idx,
    )


def test_stock_week_ends_friday():
    df = make_trading_days("2026-01-05", 5)
    weekly = daily_to_weekly(df)

    assert len(weekly) == 1
    assert weekly.index[0].weekday() == 4
    assert weekly.iloc[0]["Volume"] == 50.0
