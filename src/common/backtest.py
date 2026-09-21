from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

TRADE_COLUMNS = [
    "EntrySignalWeek",
    "EntryWeek",
    "EntryPrice",
    "ExitSignalWeek",
    "ExitWeek",
    "ExitPrice",
    "Status",
    "HoldingWeeks",
    "GrossReturn",
    "NetReturn",
    "MFE",
    "MAE",
]


def _as_bool(value: Any) -> bool:
    return False if pd.isna(value) else bool(value)


def backtest_long_transitions(
    weekly: pd.DataFrame,
    *,
    entry_column: str = "Stage2A_Event",
    exit_column: str = "Stage4A_Event",
    transaction_cost_bps_per_side: float = 0.0,
) -> pd.DataFrame:
    """Backtest long entries/exits at the next weekly open.

    Signals are observed only after their weekly bar has completed. Executing
    at the following weekly open prevents the signal bar's close from being
    used as an unattainable fill. Open trades are retained with mark-to-market
    returns and ``Status == 'open'``.
    """
    required = {"Open", "High", "Low", "Close", entry_column, exit_column}
    missing = required.difference(weekly.columns)
    if missing:
        raise ValueError(f"Backtest input is missing columns: {sorted(missing)}")
    if transaction_cost_bps_per_side < 0:
        raise ValueError("transaction_cost_bps_per_side must be >= 0")

    data = weekly.sort_index()
    cost = transaction_cost_bps_per_side / 10_000.0
    trades: list[dict[str, Any]] = []
    position: dict[str, Any] | None = None

    for signal_position in range(len(data) - 1):
        signal = data.iloc[signal_position]
        execution_position = signal_position + 1
        execution = data.iloc[execution_position]

        if position is None and _as_bool(signal[entry_column]):
            position = {
                "signal_position": signal_position,
                "entry_position": execution_position,
                "entry_signal_week": data.index[signal_position],
                "entry_week": data.index[execution_position],
                "entry_open": float(execution["Open"]),
            }
            continue

        if position is not None and _as_bool(signal[exit_column]):
            entry_position = int(position["entry_position"])
            path = data.iloc[entry_position:execution_position]
            entry_open = float(position["entry_open"])
            exit_open = float(execution["Open"])
            maximum_price = max(float(path["High"].max()), exit_open)
            minimum_price = min(float(path["Low"].min()), exit_open)
            gross_return = exit_open / entry_open - 1.0
            net_return = exit_open * (1.0 - cost) / (entry_open * (1.0 + cost)) - 1.0

            trades.append(
                {
                    "EntrySignalWeek": position["entry_signal_week"],
                    "EntryWeek": position["entry_week"],
                    "EntryPrice": entry_open,
                    "ExitSignalWeek": data.index[signal_position],
                    "ExitWeek": data.index[execution_position],
                    "ExitPrice": exit_open,
                    "Status": "closed",
                    "HoldingWeeks": execution_position - entry_position,
                    "GrossReturn": gross_return,
                    "NetReturn": net_return,
                    "MFE": maximum_price / entry_open - 1.0,
                    "MAE": minimum_price / entry_open - 1.0,
                }
            )
            position = None

    if position is not None:
        entry_position = int(position["entry_position"])
        path = data.iloc[entry_position:]
        entry_open = float(position["entry_open"])
        mark_price = float(data["Close"].iloc[-1])
        trades.append(
            {
                "EntrySignalWeek": position["entry_signal_week"],
                "EntryWeek": position["entry_week"],
                "EntryPrice": entry_open,
                "ExitSignalWeek": pd.NaT,
                "ExitWeek": data.index[-1],
                "ExitPrice": mark_price,
                "Status": "open",
                "HoldingWeeks": len(data) - 1 - entry_position,
                "GrossReturn": mark_price / entry_open - 1.0,
                "NetReturn": mark_price / (entry_open * (1.0 + cost)) - 1.0,
                "MFE": float(path["High"].max() / entry_open - 1.0),
                "MAE": float(path["Low"].min() / entry_open - 1.0),
            }
        )

    return pd.DataFrame(trades, columns=TRADE_COLUMNS)


def summarize_trades(trades: pd.DataFrame) -> pd.Series:
    """Summarize completed trades without treating an open trade as realized."""
    completed = trades.loc[trades["Status"] == "closed"] if not trades.empty else trades
    if completed.empty:
        return pd.Series(
            {
                "TradeCount": 0,
                "WinRate": np.nan,
                "MeanReturn": np.nan,
                "MedianReturn": np.nan,
                "CompoundedReturn": np.nan,
                "MaxTradeSequenceDrawdown": np.nan,
                "MeanHoldingWeeks": np.nan,
                "MeanMFE": np.nan,
                "MeanMAE": np.nan,
            }
        )

    returns = completed["NetReturn"].astype(float)
    equity = pd.concat(
        [pd.Series([1.0]), (1.0 + returns).cumprod().reset_index(drop=True)],
        ignore_index=True,
    )
    drawdown = equity / equity.cummax() - 1.0
    return pd.Series(
        {
            "TradeCount": len(completed),
            "WinRate": float((returns > 0).mean()),
            "MeanReturn": float(returns.mean()),
            "MedianReturn": float(returns.median()),
            "CompoundedReturn": float(equity.iloc[-1] - 1.0),
            "MaxTradeSequenceDrawdown": float(drawdown.min()),
            "MeanHoldingWeeks": float(completed["HoldingWeeks"].mean()),
            "MeanMFE": float(completed["MFE"].mean()),
            "MeanMAE": float(completed["MAE"].mean()),
        }
    )
