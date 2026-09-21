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
    *,
    as_of: str | pd.Timestamp | None = None,
    drop_incomplete_week: bool = True,
) -> pd.DataFrame:
    """
    Aggregate daily stock OHLCV into trading weeks ending Friday.

    Unlike crypto, a stock week may legitimately contain fewer than five
    sessions because of exchange holidays. A week is conservatively treated
    as complete only after its Friday label has passed. ``as_of`` should be
    supplied by reproducible research runs.
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
        if as_of is None:
            as_of_ts = pd.Timestamp.now(tz="UTC")
        else:
            as_of_ts = pd.Timestamp(as_of)
            if as_of_ts.tzinfo is None:
                as_of_ts = as_of_ts.tz_localize("UTC")
            else:
                as_of_ts = as_of_ts.tz_convert("UTC")

        completed = weekly.index + pd.Timedelta(days=1) <= as_of_ts
        weekly = weekly.loc[completed]

        # A newly listed security or midweek requested start can create a
        # partial first bar. Monday and Tuesday starts are retained because a
        # Monday exchange holiday is legitimate; Wednesday-or-later starts
        # are conservatively removed.
        if not weekly.empty and df.index.min().weekday() >= 2:
            days_until_friday = (4 - df.index.min().weekday()) % 7
            first_label = (
                df.index.min().normalize() + pd.Timedelta(days=days_until_friday)
            )
            weekly = weekly.loc[weekly.index != first_label]

    return weekly
