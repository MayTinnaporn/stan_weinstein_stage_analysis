import pandas as pd

from stocks.classifier import (
    classify_stock_stage,
    detect_stage2a,
    detect_stage4a,
)


def base_frame() -> pd.DataFrame:
    idx = pd.date_range(
        "2026-01-02",
        periods=4,
        freq="W-FRI",
        tz="UTC",
    )

    return pd.DataFrame(
        {
            "Close": [90.0, 120.0, 105.0, 80.0],
            "MA30": [100.0, 100.0, 100.0, 100.0],
            "MA30_slope_4w": [0.0, 0.02, 0.0, -0.02],
            "Return_26w": [-0.10, 0.10, 0.15, -0.15],
            "Breakout": [False, True, False, False],
            "Breakdown": [False, False, False, True],
            "Volume_ratio": [1.0, 1.6, 1.0, 1.2],
            "RS_Market_slope_4w": [-0.1, 0.2, 0.1, -0.2],
            "RS_Sector_slope_4w": [-0.1, 0.3, 0.1, -0.3],
        },
        index=idx,
    )


def test_stock_stage_classifier_basic_cases():
    out = classify_stock_stage(base_frame(), slope_threshold=0.01)
    assert list(out["Stage"]) == [1.0, 2.0, 3.0, 4.0]


def test_stock_stage2a_requires_positive_relative_strength():
    out = detect_stage2a(base_frame(), min_volume_ratio=1.5)
    assert bool(out["Stage2A"].iloc[1]) is True
    assert int(out["Stage2A"].sum()) == 1


def test_stock_stage4a_requires_weakening_relative_strength():
    out = detect_stage4a(base_frame())
    assert bool(out["Stage4A"].iloc[3]) is True
    assert int(out["Stage4A"].sum()) == 1
