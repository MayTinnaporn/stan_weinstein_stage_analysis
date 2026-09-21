from __future__ import annotations

import numpy as np
import pandas as pd


def classify_crypto_stage(
    df: pd.DataFrame,
    *,
    slope_threshold: float = 0.01,
) -> pd.DataFrame:
    """
    Classify each weekly observation into Stage 1/2/3/4.

    V0 heuristic:
    - Stage 2: close above MA30 and MA30 rising faster than threshold.
    - Stage 4: close below MA30 and MA30 falling faster than threshold.
    - Otherwise:
        prior 26-week return <= 0 -> Stage 1
        prior 26-week return > 0  -> Stage 3

    This is a research hypothesis, not a final Weinstein implementation.
    """
    out = df.copy()
    stage = np.full(len(out), np.nan)

    required_valid = (
        out["MA30"].notna()
        & out["MA30_slope_4w"].notna()
        & out["Return_26w"].notna()
    )

    stage2 = (
        required_valid
        & (out["Close"] > out["MA30"])
        & (out["MA30_slope_4w"] > slope_threshold)
    )

    stage4 = (
        required_valid
        & (out["Close"] < out["MA30"])
        & (out["MA30_slope_4w"] < -slope_threshold)
    )

    unresolved = required_valid & ~stage2 & ~stage4
    stage1 = unresolved & (out["Return_26w"] <= 0)
    stage3 = unresolved & (out["Return_26w"] > 0)

    stage[stage1.to_numpy()] = 1
    stage[stage2.to_numpy()] = 2
    stage[stage3.to_numpy()] = 3
    stage[stage4.to_numpy()] = 4

    out["Stage"] = stage
    return out


def detect_stage2a(
    df: pd.DataFrame,
    *,
    min_volume_ratio: float = 1.30,
) -> pd.DataFrame:
    """Flag Stage 2A breakout candidates."""
    out = df.copy()

    condition = (
        out["Breakout"].fillna(False)
        & (out["Close"] > out["MA30"])
        & (out["MA30_slope_4w"] > 0)
        & (out["Volume_ratio"] >= min_volume_ratio)
    )

    if "RS_BTC_slope_4w" in out.columns:
        condition &= out["RS_BTC_slope_4w"] > 0

    out["Stage2A"] = condition.fillna(False)
    return out


def detect_stage4a(df: pd.DataFrame) -> pd.DataFrame:
    """Flag Stage 4A breakdown candidates."""
    out = df.copy()

    condition = (
        out["Breakdown"].fillna(False)
        & (out["Close"] < out["MA30"])
        & (out["MA30_slope_4w"] < 0)
    )

    if "RS_BTC_slope_4w" in out.columns:
        condition &= out["RS_BTC_slope_4w"] < 0

    out["Stage4A"] = condition.fillna(False)
    return out
