from __future__ import annotations

import numpy as np
import pandas as pd


def _rolling_level_age(series: pd.Series, lookback: int) -> pd.Series:
    """Return weeks since the most recent rolling-window maximum.

    The input is expected to have already been shifted when the current bar
    must be excluded. Ties deliberately select the most recent occurrence.
    """
    if lookback <= 0:
        raise ValueError("lookback must be > 0")

    def age(values: np.ndarray) -> float:
        latest_maximum = np.flatnonzero(values == np.nanmax(values))[-1]
        return float(len(values) - latest_maximum)

    return series.rolling(lookback, min_periods=lookback).apply(age, raw=True)


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


def add_stage_features(
    weekly: pd.DataFrame,
    btc_weekly: pd.DataFrame | None = None,
    *,
    ma_period: int = 30,
    ma_slope_period: int = 4,
    atr_period: int = 14,
    structure_lookback: int = 26,
    volume_lookback: int = 20,
    momentum_lookback: int = 26,
    base_quality_lookback: int = 13,
    rs_lookback: int = 52,
    rs_slope_period: int = 4,
) -> pd.DataFrame:
    """
    Add V0 features used by the crypto Stage Analysis classifier.

    Support and resistance deliberately use shift(1), so the current week's
    high/low cannot define the level that the same week is breaking.
    """
    df = weekly.copy()

    df["MA30"] = df["Close"].rolling(ma_period, min_periods=ma_period).mean()

    df["MA30_slope_4w"] = df["MA30"] / df["MA30"].shift(ma_slope_period) - 1.0

    df["ATR14"] = calculate_atr(df, atr_period)

    df["MA_distance_ATR"] = (df["Close"] - df["MA30"]) / df["ATR14"].replace(
        0.0, np.nan
    )

    df["Resistance_26w"] = (
        df["High"]
        .shift(1)
        .rolling(structure_lookback, min_periods=structure_lookback)
        .max()
    )
    df["Resistance_Age_Weeks"] = _rolling_level_age(
        df["High"].shift(1),
        structure_lookback,
    )

    df["Support_26w"] = (
        df["Low"]
        .shift(1)
        .rolling(structure_lookback, min_periods=structure_lookback)
        .min()
    )

    df["Range_width_pct"] = (df["Resistance_26w"] - df["Support_26w"]) / df[
        "Close"
    ].replace(0.0, np.nan)

    df["Breakout"] = df["Close"] > df["Resistance_26w"]
    df["Breakdown"] = df["Close"] < df["Support_26w"]
    df["Breakout_Weekly_Return"] = df["Close"].pct_change(fill_method=None)
    df["Breakout_Distance_ATR"] = (df["Close"] - df["Resistance_26w"]) / df[
        "ATR14"
    ].replace(0.0, np.nan)

    prior_high = (
        df["High"]
        .shift(1)
        .rolling(base_quality_lookback, min_periods=base_quality_lookback)
        .max()
    )
    prior_low = (
        df["Low"]
        .shift(1)
        .rolling(base_quality_lookback, min_periods=base_quality_lookback)
        .min()
    )
    prior_close = df["Close"].shift(1)
    df["Prior_Base_Return"] = (
        prior_close / df["Close"].shift(base_quality_lookback + 1) - 1.0
    )
    df["Prior_Base_Range_Pct"] = (prior_high - prior_low) / prior_close.replace(
        0.0, np.nan
    )
    df["Prior_Base_Volatility"] = (
        df["Close"]
        .pct_change(fill_method=None)
        .shift(1)
        .rolling(base_quality_lookback, min_periods=base_quality_lookback)
        .std()
    )

    df["Volume_MA20"] = (
        df["Volume"]
        .shift(1)
        .rolling(volume_lookback, min_periods=volume_lookback)
        .mean()
    )

    df["Volume_ratio"] = df["Volume"] / df["Volume_MA20"].replace(0.0, np.nan)

    df["Return_26w"] = df["Close"] / df["Close"].shift(momentum_lookback) - 1.0

    if btc_weekly is not None:
        btc_close = btc_weekly["Close"].reindex(df.index).ffill()
        rs = df["Close"] / btc_close.replace(0.0, np.nan)

        df["RS_BTC"] = rs

        rs_ma = rs.rolling(rs_lookback, min_periods=rs_lookback).mean()
        df["Mansfield_RS_BTC"] = (rs / rs_ma - 1.0) * 100.0

        df["RS_BTC_slope_4w"] = df["Mansfield_RS_BTC"] - df["Mansfield_RS_BTC"].shift(
            rs_slope_period
        )

    return df
