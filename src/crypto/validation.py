from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def add_forward_returns(
    df: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 13, 26),
) -> pd.DataFrame:
    """Add forward close-to-close returns for requested weekly horizons."""
    out = df.copy()

    for horizon in horizons:
        if horizon <= 0:
            raise ValueError("forward-return horizons must be > 0")

        out[f"Forward_Return_{horizon}w"] = (
            out["Close"].shift(-horizon) / out["Close"] - 1.0
        )

    return out


def summarize_forward_returns(
    df: pd.DataFrame,
    horizons: Iterable[int] = (4, 8, 13, 26),
    state_column: str = "Stage",
) -> pd.DataFrame:
    """Summarize forward returns by a categorical state such as Stage."""
    working = add_forward_returns(df, horizons)
    rows: list[dict[str, float]] = []

    states = sorted(s for s in working[state_column].dropna().unique())

    for state in states:
        subset = working.loc[working[state_column] == state]

        for horizon in horizons:
            col = f"Forward_Return_{horizon}w"
            values = subset[col].dropna()

            if values.empty:
                continue

            rows.append(
                {
                    "State": float(state),
                    "HorizonWeeks": int(horizon),
                    "Count": int(values.shape[0]),
                    "MeanReturn": float(values.mean()),
                    "MedianReturn": float(values.median()),
                    "PositiveProbability": float((values > 0).mean()),
                    "StdReturn": float(values.std(ddof=1))
                    if values.shape[0] > 1
                    else np.nan,
                }
            )

    return pd.DataFrame(rows)
