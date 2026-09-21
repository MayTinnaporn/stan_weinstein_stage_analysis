import pandas as pd
import pytest

from crypto.validation import (
    add_forward_excursions,
    add_forward_returns,
    summarize_event_forward_returns,
    summarize_forward_returns,
)


def test_forward_returns():
    idx = pd.date_range(
        "2026-01-04",
        periods=5,
        freq="W-SUN",
        tz="UTC",
    )
    df = pd.DataFrame(
        {
            "Close": [100.0, 110.0, 120.0, 90.0, 150.0],
            "Stage": [1, 1, 2, 4, 2],
        },
        index=idx,
    )

    out = add_forward_returns(df, horizons=[1])
    assert round(out["Forward_Return_1w"].iloc[0], 6) == 0.1


def test_summary_returns_non_empty():
    idx = pd.date_range(
        "2026-01-04",
        periods=6,
        freq="W-SUN",
        tz="UTC",
    )
    df = pd.DataFrame(
        {
            "Close": [100, 110, 120, 130, 125, 140],
            "Stage": [1, 1, 2, 2, 3, 4],
        },
        index=idx,
        dtype=float,
    )

    summary = summarize_forward_returns(df, horizons=[1])

    assert not summary.empty
    assert set(summary.columns) >= {
        "State",
        "HorizonWeeks",
        "Count",
        "MeanReturn",
        "MedianReturn",
        "PositiveProbability",
        "StdReturn",
        "MeanMFE",
        "MeanMAE",
    }


def test_summary_accepts_one_shot_horizon_iterable():
    idx = pd.date_range("2026-01-04", periods=6, freq="W-SUN", tz="UTC")
    df = pd.DataFrame(
        {"Close": [100, 110, 120, 130, 125, 140], "Stage": [1, 1, 2, 2, 3, 4]},
        index=idx,
        dtype=float,
    )

    summary = summarize_forward_returns(df, horizons=(value for value in [1, 2]))

    assert set(summary["HorizonWeeks"]) == {1, 2}


def test_forward_excursions_use_future_weeks_only():
    idx = pd.date_range("2026-01-04", periods=4, freq="W-SUN", tz="UTC")
    df = pd.DataFrame(
        {
            "Close": [100.0, 105.0, 95.0, 110.0],
            "High": [101.0, 120.0, 108.0, 115.0],
            "Low": [99.0, 90.0, 80.0, 100.0],
        },
        index=idx,
    )

    out = add_forward_excursions(df, horizons=[2])

    assert out["Forward_MFE_2w"].iloc[0] == pytest.approx(0.2)
    assert out["Forward_MAE_2w"].iloc[0] == pytest.approx(-0.2)
    assert pd.isna(out["Forward_MFE_2w"].iloc[-1])


def test_event_summary_preserves_weekly_horizon_spacing():
    idx = pd.date_range("2026-01-04", periods=5, freq="W-SUN", tz="UTC")
    df = pd.DataFrame(
        {
            "Close": [100.0, 110.0, 120.0, 130.0, 140.0],
            "Stage2A_Event": [True, False, False, True, False],
        },
        index=idx,
    )

    summary = summarize_event_forward_returns(df, "Stage2A_Event", horizons=[1])

    assert summary.iloc[0]["Count"] == 2
    assert round(summary.iloc[0]["MeanReturn"], 6) == round((0.1 + 10 / 130) / 2, 6)
