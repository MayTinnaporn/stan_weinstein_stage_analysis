from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd

SUMMARY_COLUMNS = [
    "State",
    "HorizonWeeks",
    "Count",
    "MeanReturn",
    "MedianReturn",
    "PositiveProbability",
    "StdReturn",
    "MeanMFE",
    "MedianMFE",
    "MeanMAE",
    "MedianMAE",
]


def _materialize_horizons(horizons: Iterable[int]) -> tuple[int, ...]:
    values = tuple(int(horizon) for horizon in horizons)
    if any(horizon <= 0 for horizon in values):
        raise ValueError("forward-return horizons must be > 0")
    return values


def add_forward_returns(
    df: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 13, 26),
) -> pd.DataFrame:
    """Add forward close-to-close returns for requested weekly horizons."""
    out = df.copy()

    for horizon in _materialize_horizons(horizons):
        out[f"Forward_Return_{horizon}w"] = (
            out["Close"].shift(-horizon) / out["Close"] - 1.0
        )

    return out


def add_forward_excursions(
    df: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 13, 26),
) -> pd.DataFrame:
    """Add long-side maximum favorable/adverse excursions after each week.

    Excursions start with the next weekly bar and require a complete requested
    horizon. They are measured from the signal week's closing price.
    """
    missing = {"Close", "High", "Low"}.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns required for excursions: {sorted(missing)}")

    out = df.copy()

    for horizon in _materialize_horizons(horizons):
        future_highs = pd.concat(
            [out["High"].shift(-offset) for offset in range(1, horizon + 1)],
            axis=1,
        )
        future_lows = pd.concat(
            [out["Low"].shift(-offset) for offset in range(1, horizon + 1)],
            axis=1,
        )
        complete = future_highs.notna().all(axis=1) & future_lows.notna().all(axis=1)

        mfe = future_highs.max(axis=1) / out["Close"] - 1.0
        mae = future_lows.min(axis=1) / out["Close"] - 1.0

        out[f"Forward_MFE_{horizon}w"] = mfe.where(complete)
        out[f"Forward_MAE_{horizon}w"] = mae.where(complete)

    return out


def _summarize_precomputed(
    working: pd.DataFrame,
    horizons: tuple[int, ...],
    state_column: str,
    *,
    has_excursions: bool,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    states = sorted(working[state_column].dropna().unique(), key=str)

    for state in states:
        subset = working.loc[working[state_column] == state]

        for horizon in horizons:
            return_column = f"Forward_Return_{horizon}w"
            values = subset[return_column].dropna()
            if values.empty:
                continue

            mfe_values = (
                subset[f"Forward_MFE_{horizon}w"].dropna()
                if has_excursions
                else pd.Series(dtype=float)
            )
            mae_values = (
                subset[f"Forward_MAE_{horizon}w"].dropna()
                if has_excursions
                else pd.Series(dtype=float)
            )

            rows.append(
                {
                    "State": state.item() if hasattr(state, "item") else state,
                    "HorizonWeeks": horizon,
                    "Count": int(values.shape[0]),
                    "MeanReturn": float(values.mean()),
                    "MedianReturn": float(values.median()),
                    "PositiveProbability": float((values > 0).mean()),
                    "StdReturn": float(values.std(ddof=1))
                    if values.shape[0] > 1
                    else np.nan,
                    "MeanMFE": float(mfe_values.mean()) if not mfe_values.empty else np.nan,
                    "MedianMFE": float(mfe_values.median())
                    if not mfe_values.empty
                    else np.nan,
                    "MeanMAE": float(mae_values.mean()) if not mae_values.empty else np.nan,
                    "MedianMAE": float(mae_values.median())
                    if not mae_values.empty
                    else np.nan,
                }
            )

    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def summarize_forward_returns(
    df: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 13, 26),
    state_column: str = "Stage",
) -> pd.DataFrame:
    """Summarize returns and excursions by Stage or another state."""
    horizon_values = _materialize_horizons(horizons)
    working = add_forward_returns(df, horizon_values)
    has_excursion_inputs = {"High", "Low"}.issubset(working.columns)
    if has_excursion_inputs:
        working = add_forward_excursions(working, horizon_values)

    return _summarize_precomputed(
        working,
        horizon_values,
        state_column,
        has_excursions=has_excursion_inputs,
    )


def summarize_event_forward_returns(
    df: pd.DataFrame,
    event_column: str,
    horizons: Iterable[int] = (4, 8, 13, 26),
) -> pd.DataFrame:
    """Summarize forward outcomes for rows where an event is newly triggered."""
    if event_column not in df.columns:
        raise ValueError(f"Missing event column: {event_column}")

    horizon_values = _materialize_horizons(horizons)
    working = add_forward_returns(df, horizon_values)
    has_excursion_inputs = {"High", "Low"}.issubset(working.columns)
    if has_excursion_inputs:
        working = add_forward_excursions(working, horizon_values)

    events = working.loc[working[event_column].fillna(False)].copy()
    events["Event"] = event_column
    return _summarize_precomputed(
        events,
        horizon_values,
        "Event",
        has_excursions=has_excursion_inputs,
    )
