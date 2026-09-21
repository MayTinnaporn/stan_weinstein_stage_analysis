from __future__ import annotations

from typing import Any

import pandas as pd

from common.models import AnalysisBundle

LATEST_FIELDS = [
    "Close",
    "MA30",
    "MA30_slope_4w",
    "Resistance_26w",
    "Support_26w",
    "Volume_ratio",
    "Stage",
    "Stage2A",
    "Stage4A",
    "Stage2A_Event",
    "Stage4A_Event",
    "Stage_Run_ID",
    "Weeks_In_Stage",
    "Weeks_Since_Stage2A_Event",
    "Weeks_Since_Stage4A_Event",
    "Stage2A_EpisodeStart_Event",
    "Stage2A_Continuation_Event",
    "Stage2A_Confirmed_Event",
    "Stage4A_EpisodeStart_Event",
    "Stage4A_Continuation_Event",
    "Stage4A_Confirmed_Event",
]


def latest_analysis_record(bundle: AnalysisBundle) -> dict[str, Any]:
    """Flatten the latest completed analyzed week for run-level reporting."""
    if bundle.analysis.empty:
        raise ValueError(f"No analyzed weekly rows for {bundle.symbol}")

    row = bundle.analysis.iloc[-1]
    record: dict[str, Any] = {
        "AssetType": bundle.asset_type,
        "Symbol": bundle.symbol,
        "AsOf": bundle.as_of.isoformat(),
        "Week": bundle.analysis.index[-1].isoformat(),
        "PreviousStage": (
            bundle.analysis["Stage"].iloc[-2]
            if len(bundle.analysis) > 1
            else pd.NA
        ),
        "DataQuality": "ok",
    }
    for field in LATEST_FIELDS:
        record[field] = row[field] if field in row.index else pd.NA
    return record
