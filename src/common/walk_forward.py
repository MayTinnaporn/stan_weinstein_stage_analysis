from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd

EVENT_OUTCOME_COLUMNS = [
    "Symbol",
    "Event",
    "EventWeek",
    "Fold",
    "FoldStart",
    "FoldEnd",
    "HorizonWeeks",
    "OutcomeAvailable",
    "EntryClose",
    "FutureClose",
    "ForwardReturn",
    "MFE",
    "MAE",
]

EVENT_SUMMARY_COLUMNS = [
    "Symbol",
    "Event",
    "Fold",
    "HorizonWeeks",
    "Count",
    "CensoredCount",
    "MeanReturn",
    "MedianReturn",
    "PositiveProbability",
    "DirectionalSuccessProbability",
    "StdReturn",
    "MeanMFE",
    "MedianMFE",
    "MeanMAE",
    "MedianMAE",
]


def _validate_inputs(
    weekly: pd.DataFrame,
    horizons: Iterable[int],
    min_history_weeks: int,
    test_window_weeks: int,
    event_columns: Iterable[str],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    horizon_values = tuple(int(value) for value in horizons)
    event_values = tuple(event_columns)
    if not horizon_values or any(value <= 0 for value in horizon_values):
        raise ValueError("horizons must contain positive integers")
    if min_history_weeks < 0:
        raise ValueError("min_history_weeks must be >= 0")
    if test_window_weeks <= 0:
        raise ValueError("test_window_weeks must be > 0")

    required = {"Close", "High", "Low", *event_values}
    missing = required.difference(weekly.columns)
    if missing:
        raise ValueError(f"Walk-forward input is missing columns: {sorted(missing)}")
    if not weekly.index.is_monotonic_increasing:
        raise ValueError("Walk-forward input index must be sorted ascending")
    if weekly.index.has_duplicates:
        raise ValueError("Walk-forward input index must not contain duplicates")
    return horizon_values, event_values


def build_walk_forward_folds(
    weekly: pd.DataFrame,
    *,
    symbol: str,
    min_history_weeks: int = 104,
    test_window_weeks: int = 52,
) -> pd.DataFrame:
    """Create sequential evaluation blocks after an initial history period."""
    columns = ["Symbol", "Fold", "FoldStart", "FoldEnd", "Weeks"]
    if min_history_weeks < 0:
        raise ValueError("min_history_weeks must be >= 0")
    if test_window_weeks <= 0:
        raise ValueError("test_window_weeks must be > 0")
    if len(weekly) <= min_history_weeks:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []
    for start in range(min_history_weeks, len(weekly), test_window_weeks):
        end = min(start + test_window_weeks, len(weekly))
        rows.append(
            {
                "Symbol": symbol,
                "Fold": len(rows) + 1,
                "FoldStart": weekly.index[start],
                "FoldEnd": weekly.index[end - 1],
                "Weeks": end - start,
            }
        )
    return pd.DataFrame(rows, columns=columns)


def calculate_walk_forward_event_outcomes(
    weekly: pd.DataFrame,
    *,
    symbol: str,
    horizons: Iterable[int] = (4, 8, 13, 26),
    min_history_weeks: int = 104,
    test_window_weeks: int = 52,
    event_columns: Iterable[str] = ("Stage2A_Event", "Stage4A_Event"),
) -> pd.DataFrame:
    """Calculate later-bar outcomes for events in chronological test blocks.

    The classifier is not fitted or tuned inside a fold. The initial history
    period provides feature warm-up, and every subsequent event belongs to one
    non-overlapping evaluation block. An outcome is marked unavailable when its
    complete horizon has not yet elapsed.
    """
    horizon_values, event_values = _validate_inputs(
        weekly,
        horizons,
        min_history_weeks,
        test_window_weeks,
        event_columns,
    )
    data = weekly.copy()
    rows: list[dict[str, Any]] = []

    for position in range(min_history_weeks, len(data)):
        fold = (position - min_history_weeks) // test_window_weeks + 1
        fold_start_position = min_history_weeks + (fold - 1) * test_window_weeks
        fold_end_position = min(fold_start_position + test_window_weeks, len(data)) - 1

        for event_column in event_values:
            event_value = data.iloc[position][event_column]
            if pd.isna(event_value) or not bool(event_value):
                continue

            entry_close = float(data["Close"].iloc[position])
            for horizon in horizon_values:
                future_position = position + horizon
                complete = future_position < len(data)
                future_close = np.nan
                forward_return = np.nan
                mfe = np.nan
                mae = np.nan

                if complete:
                    future_close = float(data["Close"].iloc[future_position])
                    future_path = data.iloc[position + 1 : future_position + 1]
                    forward_return = future_close / entry_close - 1.0
                    mfe = float(future_path["High"].max() / entry_close - 1.0)
                    mae = float(future_path["Low"].min() / entry_close - 1.0)

                rows.append(
                    {
                        "Symbol": symbol,
                        "Event": event_column,
                        "EventWeek": data.index[position],
                        "Fold": fold,
                        "FoldStart": data.index[fold_start_position],
                        "FoldEnd": data.index[fold_end_position],
                        "HorizonWeeks": horizon,
                        "OutcomeAvailable": complete,
                        "EntryClose": entry_close,
                        "FutureClose": future_close,
                        "ForwardReturn": forward_return,
                        "MFE": mfe,
                        "MAE": mae,
                    }
                )

    return pd.DataFrame(rows, columns=EVENT_OUTCOME_COLUMNS)


def summarize_walk_forward_outcomes(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Summarize complete outcomes by fold and across all folds."""
    missing = set(EVENT_OUTCOME_COLUMNS).difference(outcomes.columns)
    if missing:
        raise ValueError(f"Outcome table is missing columns: {sorted(missing)}")
    if outcomes.empty:
        return pd.DataFrame(columns=EVENT_SUMMARY_COLUMNS)

    rows: list[dict[str, Any]] = []
    group_columns = ["Symbol", "Event", "Fold", "HorizonWeeks"]
    grouped_inputs = [(False, outcomes)]
    all_folds = outcomes.copy()
    all_folds["Fold"] = "ALL"
    grouped_inputs.append((True, all_folds))

    for _, table in grouped_inputs:
        for keys, group in table.groupby(group_columns, sort=True, dropna=False):
            symbol, event, fold, horizon = keys
            observed = group.loc[group["OutcomeAvailable"].astype(bool)]
            returns = observed["ForwardReturn"].astype(float)
            directional_success = (
                returns < 0 if str(event).startswith("Stage4A") else returns > 0
            )
            rows.append(
                {
                    "Symbol": symbol,
                    "Event": event,
                    "Fold": fold,
                    "HorizonWeeks": int(horizon),
                    "Count": len(observed),
                    "CensoredCount": len(group) - len(observed),
                    "MeanReturn": float(returns.mean()) if not returns.empty else np.nan,
                    "MedianReturn": float(returns.median())
                    if not returns.empty
                    else np.nan,
                    "PositiveProbability": float((returns > 0).mean())
                    if not returns.empty
                    else np.nan,
                    "DirectionalSuccessProbability": float(
                        directional_success.mean()
                    )
                    if not returns.empty
                    else np.nan,
                    "StdReturn": float(returns.std(ddof=1))
                    if len(returns) > 1
                    else np.nan,
                    "MeanMFE": float(observed["MFE"].mean())
                    if not observed.empty
                    else np.nan,
                    "MedianMFE": float(observed["MFE"].median())
                    if not observed.empty
                    else np.nan,
                    "MeanMAE": float(observed["MAE"].mean())
                    if not observed.empty
                    else np.nan,
                    "MedianMAE": float(observed["MAE"].median())
                    if not observed.empty
                    else np.nan,
                }
            )

    return pd.DataFrame(rows, columns=EVENT_SUMMARY_COLUMNS)
