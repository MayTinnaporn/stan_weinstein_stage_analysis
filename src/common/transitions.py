from __future__ import annotations

import pandas as pd


def add_transition_events(df: pd.DataFrame) -> pd.DataFrame:
    """Add rising-edge events for Stage 2A and Stage 4A candidates.

    Candidate flags may remain true for multiple consecutive weeks. The event
    columns are true only in the first such week, which prevents duplicate
    alerts while preserving the underlying candidate state for research.
    """
    out = df.copy()

    for candidate_column, event_column in (
        ("Stage2A", "Stage2A_Event"),
        ("Stage4A", "Stage4A_Event"),
    ):
        if candidate_column not in out.columns:
            raise ValueError(f"Missing transition candidate column: {candidate_column}")

        candidate = out[candidate_column].fillna(False).astype(bool)
        previous = candidate.shift(1, fill_value=False)
        out[event_column] = candidate & ~previous

    return out
