from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_stage_analysis(
    df: pd.DataFrame,
    symbol: str,
    output_path: str | Path | None = None,
):
    """Plot weekly stock price, Stage features and transition candidates."""
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(df.index, df["Close"], label="Weekly Close")
    ax.plot(df.index, df["MA30"], label="30W SMA")
    ax.plot(df.index, df["Resistance_26w"], label="26W Resistance", linestyle="--")
    ax.plot(df.index, df["Support_26w"], label="26W Support", linestyle="--")

    for stage in (1, 2, 3, 4):
        mask = df["Stage"] == stage
        if mask.any():
            ax.scatter(
                df.index[mask],
                df.loc[mask, "Close"],
                s=12,
                label=f"Stage {stage}",
            )

    if "Stage2A" in df.columns:
        mask = df["Stage2A"].fillna(False)
        if mask.any():
            ax.scatter(
                df.index[mask],
                df.loc[mask, "Close"],
                marker="^",
                s=80,
                label="Stage 2A candidate",
            )

    if "Stage4A" in df.columns:
        mask = df["Stage4A"].fillna(False)
        if mask.any():
            ax.scatter(
                df.index[mask],
                df.loc[mask, "Close"],
                marker="v",
                s=80,
                label="Stage 4A candidate",
            )

    ax.set_title(f"{symbol} - Stock Stage Analysis V0")
    ax.set_xlabel("Week")
    ax.set_ylabel("Adjusted Price")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.25)

    fig.tight_layout()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig, ax
