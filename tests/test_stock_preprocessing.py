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


def test_stock_friday_bar_is_not_complete_until_saturday_utc():
    df = make_trading_days("2026-01-05", 5)

    friday_run = daily_to_weekly(df, as_of="2026-01-09T22:00:00Z")
    saturday_run = daily_to_weekly(df, as_of="2026-01-10T00:00:00Z")

    assert friday_run.empty
    assert len(saturday_run) == 1


def test_midweek_first_stock_bar_is_removed():
    df = make_trading_days("2026-01-07", 8)
    weekly = daily_to_weekly(df, as_of="2026-01-17T00:00:00Z")

    assert list(weekly.index) == [pd.Timestamp("2026-01-16", tz="UTC")]
