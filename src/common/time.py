from __future__ import annotations

import pandas as pd


def to_utc_timestamp(value: str | pd.Timestamp | None = None) -> pd.Timestamp:
    """Return a timezone-aware UTC timestamp, defaulting to current time."""
    if value is None:
        return pd.Timestamp.now(tz="UTC")

    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
