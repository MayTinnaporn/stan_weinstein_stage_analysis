from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}


def validate_ohlcv(df: pd.DataFrame) -> None:
    """Validate the minimum OHLCV structure expected by the pipeline."""
    missing = REQUIRED_OHLCV_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("OHLCV index must be a pandas DatetimeIndex")

    if df.index.tz is None:
        raise ValueError("OHLCV DatetimeIndex must be timezone-aware")

    if df.index.has_duplicates:
        raise ValueError("OHLCV DatetimeIndex contains duplicate timestamps")

    if not df.index.is_monotonic_increasing:
        raise ValueError("OHLCV DatetimeIndex must be sorted ascending")


def daily_to_weekly(
    df: pd.DataFrame,
    week_rule: str = "W-SUN",
    drop_incomplete_week: bool = True,
) -> pd.DataFrame:
    """
    Aggregate daily crypto OHLCV into weekly bars.

    W-SUN produces Monday-through-Sunday weeks labeled by Sunday.

    If drop_incomplete_week is True, the final weekly bar is retained only
    when the input includes the Sunday corresponding to that weekly label.
    """
    validate_ohlcv(df)

    weekly = (
        df.resample(week_rule)
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna(subset=["Open", "High", "Low", "Close"])
    )

    if drop_incomplete_week and not weekly.empty:
        last_daily_date = df.index.max().normalize()
        weekly = weekly.loc[weekly.index.normalize() <= last_daily_date]

    return weekly
