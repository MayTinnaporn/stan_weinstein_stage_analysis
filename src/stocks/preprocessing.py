from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}


def validate_ohlcv(df: pd.DataFrame) -> None:
    """Validate the minimum stock OHLCV structure expected by the pipeline."""
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
    week_rule: str = "W-FRI",
) -> pd.DataFrame:
    """
    Aggregate daily stock OHLCV into trading weeks ending Friday.

    Unlike crypto, a stock week may legitimately contain fewer than five
    sessions because of exchange holidays. Therefore the function does not
    require five observations per week.
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

    # If the most recent daily session belongs to a future Friday label,
    # that resampled bar is a partial current trading week. Remove it.
    if not weekly.empty:
        last_daily = df.index.max().normalize()
        current_week_label = weekly.index.max().normalize()
        if current_week_label > last_daily:
            weekly = weekly.iloc[:-1]

    return weekly
