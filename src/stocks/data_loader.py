from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_daily_ohlcv(
    symbol: str,
    start: str,
    end: str | None = None,
    *,
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """
    Download daily stock OHLCV using yfinance.

    Parameters
    ----------
    symbol:
        Ticker such as AAPL, SPY, SMH.
    start:
        Inclusive start date.
    end:
        Optional end date. yfinance treats end as exclusive, so one extra day
        is requested internally when an explicit end is provided.
    auto_adjust:
        If True, yfinance adjusts OHLC for splits and dividends.

    Returns
    -------
    pd.DataFrame
        Daily OHLCV with a timezone-aware UTC DatetimeIndex.

    Notes
    -----
    For Stage Analysis research, adjusted data prevents stock splits from
    appearing as artificial price collapses. The exact dividend-adjustment
    convention should remain documented because price-trend research and
    total-return research are not identical questions.
    """
    start_ts = pd.Timestamp(start)

    if end is None:
        end_arg = None
    else:
        end_arg = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(
        "Fetching %s daily OHLCV with yfinance from %s to %s",
        symbol,
        start,
        end if end is not None else "latest complete available session",
    )

    df = yf.download(
        symbol,
        start=start_ts.strftime("%Y-%m-%d"),
        end=end_arg,
        auto_adjust=auto_adjust,
        progress=False,
        actions=False,
        threads=False,
    )

    if df.empty:
        raise ValueError(f"No stock OHLCV returned for {symbol}")

    # yfinance may return MultiIndex columns even for a single ticker.
    if isinstance(df.columns, pd.MultiIndex):
        if symbol in df.columns.get_level_values(-1):
            df = df.xs(symbol, axis=1, level=-1)
        else:
            df.columns = df.columns.get_level_values(0)

    expected = ["Open", "High", "Low", "Close", "Volume"]
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns for {symbol}: {missing}")

    df = df[expected].copy()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    idx = pd.DatetimeIndex(df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")

    df.index = idx
    df.index.name = "timestamp"

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    return df.sort_index()
