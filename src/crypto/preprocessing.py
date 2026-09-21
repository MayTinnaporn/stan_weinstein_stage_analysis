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

    When ``drop_incomplete_week`` is true, boundary weeks with fewer than
    seven distinct UTC dates are removed. An incomplete week inside the data
    range is treated as a data-quality failure rather than silently skipped.
    """
    validate_ohlcv(df)

    distinct_dates = pd.Series(
        df.index.normalize(),
        index=df.index,
    ).resample(week_rule).nunique()

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
        incomplete = distinct_dates.reindex(weekly.index, fill_value=0) != 7
        internal_incomplete = incomplete.iloc[1:-1]

        if internal_incomplete.any():
            labels = internal_incomplete.index[internal_incomplete]
            formatted = ", ".join(label.date().isoformat() for label in labels)
            raise ValueError(f"Incomplete internal crypto week(s): {formatted}")

        weekly = weekly.loc[~incomplete]

    return weekly
