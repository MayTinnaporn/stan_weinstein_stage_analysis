from __future__ import annotations

import logging

import ccxt
import pandas as pd

logger = logging.getLogger(__name__)


def _to_utc_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def fetch_daily_ohlcv(
    symbol: str,
    start: str,
    end: str | None = None,
    exchange_id: str = "binance",
) -> pd.DataFrame:
    """
    Download daily OHLCV from a CCXT-compatible exchange.

    The returned DataFrame is UTC-indexed and contains
    Open/High/Low/Close/Volume columns.

    If end is omitted, yesterday UTC is used so today's unfinished
    daily candle is not included.
    """
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"Unknown CCXT exchange_id: {exchange_id}")

    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})

    start_ts = _to_utc_timestamp(start).normalize()

    if end is None:
        end_ts = pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=1)
    else:
        end_ts = _to_utc_timestamp(end).normalize()

    if start_ts > end_ts:
        raise ValueError("start must be <= end")

    since = int(start_ts.timestamp() * 1000)
    end_ms = int(end_ts.timestamp() * 1000)
    rows: list[list[float]] = []

    logger.info(
        "Fetching %s daily OHLCV from %s (%s to %s)",
        symbol,
        exchange_id,
        start_ts.date(),
        end_ts.date(),
    )

    while since <= end_ms:
        batch = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe="1d",
            since=since,
            limit=1000,
        )

        if not batch:
            break

        rows.extend(batch)

        last_timestamp = int(batch[-1][0])
        next_since = last_timestamp + 86_400_000

        if last_timestamp >= end_ms or next_since <= since:
            break

        since = next_since

    if not rows:
        raise ValueError(
            f"No OHLCV returned for {symbol} from {exchange_id} "
            f"between {start_ts.date()} and {end_ts.date()}."
        )

    df = pd.DataFrame(
        rows,
        columns=["timestamp", "Open", "High", "Low", "Close", "Volume"],
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    df = (
        df.drop_duplicates("timestamp", keep="last")
        .set_index("timestamp")
        .sort_index()
    )

    df = df.loc[(df.index >= start_ts) & (df.index <= end_ts)]

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    return df
