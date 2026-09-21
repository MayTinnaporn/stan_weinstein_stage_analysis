from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate simple-moving-average Average True Range."""
    if period <= 0:
        raise ValueError("period must be > 0")

    previous_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(period, min_periods=period).mean()


def calculate_mansfield_rs(
    asset_close: pd.Series,
    benchmark_close: pd.Series,
    *,
    rs_lookback: int = 52,
    rs_slope_period: int = 4,
    prefix: str = "Market",
) -> pd.DataFrame:
    """
    Calculate Mansfield-style relative strength and its slope.

    Formula
    -------
    RS = Asset Close / Benchmark Close

    Mansfield RS = (RS / rolling_mean(RS, 52) - 1) * 100

    The 52-week lookback is configurable and should be treated as a research
    parameter rather than an immutable rule in this quantitative adaptation.
    """
    benchmark = benchmark_close.reindex(asset_close.index).ffill()

    rs = asset_close / benchmark.replace(0.0, np.nan)
    rs_ma = rs.rolling(rs_lookback, min_periods=rs_lookback).mean()
    mansfield = (rs / rs_ma - 1.0) * 100.0
    slope = mansfield - mansfield.shift(rs_slope_period)

    return pd.DataFrame(
        {
            f"RS_{prefix}": rs,
            f"Mansfield_RS_{prefix}": mansfield,
            f"RS_{prefix}_slope_4w": slope,
        },
        index=asset_close.index,
    )


def add_stage_features(
    weekly: pd.DataFrame,
    market_weekly: pd.DataFrame | None = None,
    sector_weekly: pd.DataFrame | None = None,
    *,
    ma_period: int = 30,
    ma_slope_period: int = 4,
    atr_period: int = 14,
    structure_lookback: int = 26,
    volume_lookback: int = 20,
    momentum_lookback: int = 26,
    rs_lookback: int = 52,
    rs_slope_period: int = 4,
) -> pd.DataFrame:
    """
    Add V0 stock features.

    Support/resistance and volume baseline deliberately use shift(1) to
    prevent the current week from defining the level it is simultaneously
    breaking.
    """
    df = weekly.copy()

    df["MA30"] = df["Close"].rolling(
        ma_period, min_periods=ma_period
    ).mean()

    df["MA30_slope_4w"] = (
        df["MA30"] / df["MA30"].shift(ma_slope_period) - 1.0
    )

    df["ATR14"] = calculate_atr(df, atr_period)

    df["MA_distance_ATR"] = (
        (df["Close"] - df["MA30"])
        / df["ATR14"].replace(0.0, np.nan)
    )

    df["Resistance_26w"] = (
        df["High"]
        .shift(1)
        .rolling(structure_lookback, min_periods=structure_lookback)
        .max()
    )

    df["Support_26w"] = (
        df["Low"]
        .shift(1)
        .rolling(structure_lookback, min_periods=structure_lookback)
        .min()
    )

    df["Range_width_pct"] = (
        (df["Resistance_26w"] - df["Support_26w"])
        / df["Close"].replace(0.0, np.nan)
    )

    df["Breakout"] = df["Close"] > df["Resistance_26w"]
    df["Breakdown"] = df["Close"] < df["Support_26w"]

    df["Volume_MA20"] = (
        df["Volume"]
        .shift(1)
        .rolling(volume_lookback, min_periods=volume_lookback)
        .mean()
    )

    df["Volume_ratio"] = (
        df["Volume"] / df["Volume_MA20"].replace(0.0, np.nan)
    )

    df["Return_26w"] = (
        df["Close"] / df["Close"].shift(momentum_lookback) - 1.0
    )

    df["Up_week"] = df["Close"] > df["Close"].shift(1)
    df["Up_volume"] = np.where(df["Up_week"], df["Volume"], 0.0)
    df["Down_volume"] = np.where(~df["Up_week"], df["Volume"], 0.0)

    if market_weekly is not None:
        market_rs = calculate_mansfield_rs(
            df["Close"],
            market_weekly["Close"],
            rs_lookback=rs_lookback,
            rs_slope_period=rs_slope_period,
            prefix="Market",
        )
        df = df.join(market_rs)

    if sector_weekly is not None:
        sector_rs = calculate_mansfield_rs(
            df["Close"],
            sector_weekly["Close"],
            rs_lookback=rs_lookback,
            rs_slope_period=rs_slope_period,
            prefix="Sector",
        )
        df = df.join(sector_rs)

    return df
