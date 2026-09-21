import pandas as pd

from crypto.validation import add_forward_returns, summarize_forward_returns


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
    }
