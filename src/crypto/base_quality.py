from __future__ import annotations

from typing import Any

import pandas as pd

BASE_QUALITY_FEATURES = (
    "Stage1_Weeks_Prior_Window",
    "Weeks_Since_Stage1",
    "Prior_Base_Return",
    "Prior_Base_Range_Pct",
    "Prior_Base_Volatility",
    "Resistance_Age_Weeks",
    "Breakout_Weekly_Return",
    "Breakout_Distance_ATR",
    "MA_distance_ATR",
    "Volume_ratio",
    "Range_width_pct",
    "RS_BTC_slope_4w",
)

BASE_QUALITY_LABELS = (
    "Stage2A_EpisodeStart_Event",
    "Stage2A_RecentStage1_Event",
    "Stage2A_NoRecentStage1_Event",
)


def build_stage2a_base_quality_dataset(
    analysis: pd.DataFrame,
    outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Attach causal event-week diagnostics to Stage 2A V0 outcomes."""
    stage2a = outcomes.loc[outcomes["Event"] == "Stage2A_Event"].copy()
    diagnostic_columns = [*BASE_QUALITY_LABELS, *BASE_QUALITY_FEATURES]
    diagnostics_source = analysis.copy()
    for column in diagnostic_columns:
        if column not in diagnostics_source.columns:
            diagnostics_source[column] = pd.NA

    diagnostics = diagnostics_source.loc[:, diagnostic_columns].copy()
    diagnostics.index.name = "EventWeek"
    diagnostics = diagnostics.reset_index()
    if stage2a.empty:
        return stage2a.merge(diagnostics, on="EventWeek", how="left")
    return stage2a.merge(
        diagnostics, on="EventWeek", how="left", validate="many_to_one"
    )


def summarize_base_quality_features(dataset: pd.DataFrame) -> pd.DataFrame:
    """Compare diagnostic distributions for positive and non-positive outcomes."""
    columns = [
        "HorizonWeeks",
        "DirectionalSuccess",
        "Feature",
        "Count",
        "Median",
        "Mean",
    ]
    if dataset.empty:
        return pd.DataFrame(columns=columns)

    observed = dataset.loc[dataset["OutcomeAvailable"].astype(bool)].copy()
    observed["DirectionalSuccess"] = observed["ForwardReturn"] > 0
    rows: list[dict[str, Any]] = []
    for (horizon, success), group in observed.groupby(
        ["HorizonWeeks", "DirectionalSuccess"],
        sort=True,
    ):
        for feature in BASE_QUALITY_FEATURES:
            if feature not in group.columns:
                continue
            values = pd.to_numeric(group[feature], errors="coerce").dropna()
            rows.append(
                {
                    "HorizonWeeks": int(horizon),
                    "DirectionalSuccess": bool(success),
                    "Feature": feature,
                    "Count": len(values),
                    "Median": float(values.median())
                    if not values.empty
                    else float("nan"),
                    "Mean": float(values.mean()) if not values.empty else float("nan"),
                }
            )
    return pd.DataFrame(rows, columns=columns)
