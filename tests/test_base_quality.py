import pandas as pd

from crypto.base_quality import (
    build_stage2a_base_quality_dataset,
    summarize_base_quality_features,
)


def test_base_quality_dataset_uses_event_week_diagnostics():
    index = pd.date_range("2025-01-05", periods=2, freq="W-SUN", tz="UTC")
    analysis = pd.DataFrame(
        {
            "Prior_Base_Return": [0.1, 0.9],
            "Stage2A_EpisodeStart_Event": [True, False],
            "Stage2A_RecentStage1_Event": [True, False],
            "Stage2A_NoRecentStage1_Event": [False, False],
        },
        index=index,
    )
    outcomes = pd.DataFrame(
        {
            "Event": ["Stage2A_Event"],
            "EventWeek": [index[0]],
            "OutcomeAvailable": [True],
            "HorizonWeeks": [4],
            "ForwardReturn": [0.2],
        }
    )

    dataset = build_stage2a_base_quality_dataset(analysis, outcomes)

    assert dataset.loc[0, "Prior_Base_Return"] == 0.1
    assert bool(dataset.loc[0, "Stage2A_RecentStage1_Event"])


def test_base_quality_summary_separates_positive_and_non_positive_outcomes():
    dataset = pd.DataFrame(
        {
            "OutcomeAvailable": [True, True, False],
            "HorizonWeeks": [4, 4, 4],
            "ForwardReturn": [0.2, -0.1, 0.5],
            "Prior_Base_Return": [0.3, -0.2, 9.0],
        }
    )

    summary = summarize_base_quality_features(dataset)
    prior_return = summary.loc[summary["Feature"] == "Prior_Base_Return"]

    assert len(prior_return) == 2
    success = prior_return.loc[prior_return["DirectionalSuccess"]].iloc[0]
    failure = prior_return.loc[~prior_return["DirectionalSuccess"]].iloc[0]
    assert success["Median"] == 0.3
    assert failure["Median"] == -0.2
