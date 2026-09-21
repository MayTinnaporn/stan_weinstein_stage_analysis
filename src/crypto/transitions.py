from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _stage_run_diagnostics(stage: pd.Series) -> tuple[pd.Series, pd.Series]:
    run_ids: list[object] = []
    weeks_in_stage: list[object] = []
    previous_stage: object = None
    run_id = 0
    run_length = 0

    for value in stage:
        if pd.isna(value):
            run_ids.append(pd.NA)
            weeks_in_stage.append(pd.NA)
            previous_stage = None
            run_length = 0
            continue

        if previous_stage is None or value != previous_stage:
            run_id += 1
            run_length = 1
        else:
            run_length += 1
        run_ids.append(run_id)
        weeks_in_stage.append(run_length)
        previous_stage = value

    return (
        pd.Series(run_ids, index=stage.index, dtype="Int64"),
        pd.Series(weeks_in_stage, index=stage.index, dtype="Int64"),
    )


def _weeks_since_event(event: pd.Series) -> pd.Series:
    values: list[object] = []
    last_position: int | None = None
    for position, is_event in enumerate(event.fillna(False).astype(bool)):
        values.append(pd.NA if last_position is None else position - last_position)
        if is_event:
            last_position = position
    return pd.Series(values, index=event.index, dtype="Int64")


def _weeks_since_stage(stage: pd.Series, target_stage: int) -> pd.Series:
    """Return completed weeks since the latest occurrence of a Stage."""
    values: list[object] = []
    last_position: int | None = None
    for position, stage_value in enumerate(stage):
        values.append(pd.NA if last_position is None else position - last_position)
        if not pd.isna(stage_value) and int(stage_value) == target_stage:
            last_position = position
            values[-1] = 0
    return pd.Series(values, index=stage.index, dtype="Int64")


def _classify_episode_events(
    stage: pd.Series,
    event: pd.Series,
    opposite_event: pd.Series,
    *,
    rearm_stages: Iterable[int],
) -> tuple[pd.Series, pd.Series, pd.Series]:
    rearm_values = {int(value) for value in rearm_stages}
    starts: list[bool] = []
    continuations: list[bool] = []
    episode_ids: list[object] = []
    armed = True
    active_episode: int | None = None
    episode_number = 0

    for stage_value, is_event, is_opposite in zip(
        stage,
        event.fillna(False).astype(bool),
        opposite_event.fillna(False).astype(bool),
        strict=True,
    ):
        should_rearm = (
            not pd.isna(stage_value) and int(stage_value) in rearm_values
        ) or bool(is_opposite)
        if should_rearm:
            armed = True
            active_episode = None

        start = bool(is_event) and armed
        continuation = bool(is_event) and not armed
        if start:
            episode_number += 1
            active_episode = episode_number
            armed = False

        starts.append(start)
        continuations.append(continuation)
        episode_ids.append(active_episode if active_episode is not None else pd.NA)

    index = stage.index
    return (
        pd.Series(starts, index=index, dtype=bool),
        pd.Series(continuations, index=index, dtype=bool),
        pd.Series(episode_ids, index=index, dtype="Int64"),
    )


def add_crypto_transition_semantics(
    df: pd.DataFrame,
    *,
    stage2_rearm_stages: Iterable[int] = (1, 4),
    stage4_rearm_stages: Iterable[int] = (2, 3),
    recent_stage1_lookback_weeks: int = 13,
    recent_stage1_min_weeks: int = 1,
) -> pd.DataFrame:
    """Add causal episode and next-week confirmation diagnostics.

    Existing V0 candidates and rising-edge events are preserved. An episode
    start is the first same-direction V0 event after a direction-specific re-arm;
    subsequent events are continuations. Confirmation is assessed one completed
    week later and requires the directional Stage plus a close that still holds
    beyond the original breakout/breakdown level.
    """
    required = {
        "Close",
        "Stage",
        "Resistance_26w",
        "Support_26w",
        "Stage2A_Event",
        "Stage4A_Event",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(
            f"Transition semantics input is missing columns: {sorted(missing)}"
        )
    if recent_stage1_lookback_weeks <= 0:
        raise ValueError("recent_stage1_lookback_weeks must be > 0")
    if recent_stage1_min_weeks <= 0:
        raise ValueError("recent_stage1_min_weeks must be > 0")

    out = df.copy()
    out["Stage_Run_ID"], out["Weeks_In_Stage"] = _stage_run_diagnostics(out["Stage"])
    out["Weeks_Since_Stage2A_Event"] = _weeks_since_event(out["Stage2A_Event"])
    out["Weeks_Since_Stage4A_Event"] = _weeks_since_event(out["Stage4A_Event"])
    out["Weeks_Since_Stage1"] = _weeks_since_stage(out["Stage"], 1)
    out["Stage1_Weeks_Prior_Window"] = (
        out["Stage"]
        .eq(1)
        .shift(1)
        .rolling(
            recent_stage1_lookback_weeks,
            min_periods=recent_stage1_lookback_weeks,
        )
        .sum()
        .astype("Int64")
    )

    for direction, opposite, rearm_stages in (
        ("Stage2A", "Stage4A", stage2_rearm_stages),
        ("Stage4A", "Stage2A", stage4_rearm_stages),
    ):
        starts, continuations, episode_ids = _classify_episode_events(
            out["Stage"],
            out[f"{direction}_Event"],
            out[f"{opposite}_Event"],
            rearm_stages=rearm_stages,
        )
        out[f"{direction}_EpisodeStart_Event"] = starts
        out[f"{direction}_Continuation_Event"] = continuations
        out[f"{direction}_Episode_ID"] = episode_ids

    stage2_evaluation = out["Stage2A_EpisodeStart_Event"].shift(1, fill_value=False)
    stage2_level = out["Resistance_26w"].shift(1)
    stage2_confirmed = (
        stage2_evaluation & (out["Stage"] == 2) & (out["Close"] > stage2_level)
    ).fillna(False)
    out["Stage2A_Confirmation_Evaluated"] = stage2_evaluation.astype(bool)
    out["Stage2A_Confirmation_Level"] = stage2_level.where(stage2_evaluation)
    out["Stage2A_Confirmed_Event"] = stage2_confirmed.astype(bool)
    out["Stage2A_FailedConfirmation_Event"] = (
        stage2_evaluation & ~stage2_confirmed
    ).astype(bool)

    recent_stage1 = (
        out["Stage1_Weeks_Prior_Window"] >= recent_stage1_min_weeks
    ).fillna(False)
    out["Stage2A_RecentStage1_Event"] = (
        out["Stage2A_EpisodeStart_Event"] & recent_stage1
    ).astype(bool)
    out["Stage2A_NoRecentStage1_Event"] = (
        out["Stage2A_EpisodeStart_Event"] & ~recent_stage1
    ).astype(bool)
    out["Stage2A_ConfirmedRecentStage1_Event"] = (
        out["Stage2A_Confirmed_Event"]
        & out["Stage2A_RecentStage1_Event"].shift(1, fill_value=False)
    ).astype(bool)

    stage4_evaluation = out["Stage4A_EpisodeStart_Event"].shift(1, fill_value=False)
    stage4_level = out["Support_26w"].shift(1)
    stage4_confirmed = (
        stage4_evaluation & (out["Stage"] == 4) & (out["Close"] < stage4_level)
    ).fillna(False)
    out["Stage4A_Confirmation_Evaluated"] = stage4_evaluation.astype(bool)
    out["Stage4A_Confirmation_Level"] = stage4_level.where(stage4_evaluation)
    out["Stage4A_Confirmed_Event"] = stage4_confirmed.astype(bool)
    out["Stage4A_FailedConfirmation_Event"] = (
        stage4_evaluation & ~stage4_confirmed
    ).astype(bool)

    return out
