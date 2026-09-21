from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AnalysisBundle:
    """Raw, weekly, and analyzed data produced by one reproducible run."""

    asset_type: str
    symbol: str
    as_of: pd.Timestamp
    daily: pd.DataFrame
    weekly: pd.DataFrame
    analysis: pd.DataFrame


@dataclass(frozen=True)
class BatchRunResult:
    """Paths and tables produced by a multi-asset research run."""

    run_directory: str
    latest_results: pd.DataFrame
    signals: pd.DataFrame
    failures: pd.DataFrame
