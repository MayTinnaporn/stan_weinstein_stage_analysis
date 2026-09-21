import pandas as pd
import pytest

from crypto.preprocessing import daily_to_weekly


def make_daily(start: str, periods: int) -> pd.DataFrame:
    idx = pd.date_range(start, periods=periods, freq="D", tz="UTC")
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


def test_daily_to_weekly_monday_sunday_aggregation():
    df = make_daily("2026-01-05", 7)
    weekly = daily_to_weekly(df)

    assert len(weekly) == 1
    row = weekly.iloc[0]

    assert row["Open"] == 1.0
    assert row["High"] == 8.0
    assert row["Low"] == 0.0
    assert row["Close"] == 7.5
    assert row["Volume"] == 70.0


def test_incomplete_final_week_is_removed():
    df = make_daily("2026-01-05", 6)
    weekly = daily_to_weekly(df)
    assert weekly.empty


def test_incomplete_first_week_is_removed():
    df = make_daily("2026-01-07", 12)
    weekly = daily_to_weekly(df)

    assert list(weekly.index) == [pd.Timestamp("2026-01-18", tz="UTC")]


def test_incomplete_internal_week_raises_data_quality_error():
    df = make_daily("2026-01-05", 21)
    df = df.drop(pd.Timestamp("2026-01-14", tz="UTC"))

    with pytest.raises(ValueError, match="Incomplete internal crypto week"):
        daily_to_weekly(df)
