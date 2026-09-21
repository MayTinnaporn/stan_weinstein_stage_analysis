import json

import pandas as pd
import pytest

from common.snapshots import config_hash
from common.walk_forward import (
    build_walk_forward_folds,
    calculate_walk_forward_event_outcomes,
    summarize_walk_forward_outcomes,
)
from crypto.walk_forward import run_crypto_walk_forward_validation


def make_analysis() -> pd.DataFrame:
    index = pd.date_range("2025-01-05", periods=8, freq="W-SUN", tz="UTC")
    return pd.DataFrame(
        {
            "Open": [99, 101, 109, 119, 129, 124, 139, 149],
            "High": [103, 112, 121, 135, 132, 142, 151, 161],
            "Low": [95, 98, 105, 115, 120, 122, 135, 145],
            "Close": [100, 110, 120, 130, 125, 140, 150, 160],
            "MA30": [100] * 8,
            "Stage2A_Event": [False, False, True, False, False, False, True, False],
            "Stage4A_Event": [False, False, False, False, True, False, False, False],
        },
        index=index,
    )


def test_walk_forward_outcomes_use_later_bars_and_preserve_censoring():
    analysis = make_analysis()

    outcomes = calculate_walk_forward_event_outcomes(
        analysis,
        symbol="BTC/USDT",
        horizons=[1, 2],
        min_history_weeks=2,
        test_window_weeks=3,
    )

    first = outcomes.loc[
        (outcomes["EventWeek"] == analysis.index[2])
        & (outcomes["Event"] == "Stage2A_Event")
        & (outcomes["HorizonWeeks"] == 2)
    ].iloc[0]
    assert first["Fold"] == 1
    assert first["ForwardReturn"] == pytest.approx(125 / 120 - 1)
    assert first["MFE"] == pytest.approx(135 / 120 - 1)
    assert first["MAE"] == pytest.approx(115 / 120 - 1)

    censored = outcomes.loc[
        (outcomes["EventWeek"] == analysis.index[6])
        & (outcomes["HorizonWeeks"] == 2)
    ].iloc[0]
    assert not censored["OutcomeAvailable"]
    assert pd.isna(censored["ForwardReturn"])


def test_walk_forward_folds_and_summary_are_chronological():
    analysis = make_analysis()
    folds = build_walk_forward_folds(
        analysis,
        symbol="BTC/USDT",
        min_history_weeks=2,
        test_window_weeks=3,
    )
    outcomes = calculate_walk_forward_event_outcomes(
        analysis,
        symbol="BTC/USDT",
        horizons=[2],
        min_history_weeks=2,
        test_window_weeks=3,
    )
    summary = summarize_walk_forward_outcomes(outcomes)

    assert list(folds["Weeks"]) == [3, 3]
    all_folds = summary.loc[summary["Fold"] == "ALL"]
    stage2a = all_folds.loc[all_folds["Event"] == "Stage2A_Event"].iloc[0]
    assert stage2a["Count"] == 1
    assert stage2a["CensoredCount"] == 1
    assert stage2a["DirectionalSuccessProbability"] == 1.0

    stage4a = all_folds.loc[all_folds["Event"] == "Stage4A_Event"].iloc[0]
    assert stage4a["DirectionalSuccessProbability"] == 0.0


def test_crypto_validation_writes_reproducible_report(tmp_path):
    config = {"research": {"forward_return_horizons": [1, 2]}}
    crypto_directory = tmp_path / "run" / "crypto"
    asset_directory = crypto_directory / "BTC_USDT"
    asset_directory.mkdir(parents=True)
    make_analysis().to_csv(asset_directory / "analysis.csv")
    (asset_directory / "metadata.json").write_text(
        json.dumps({"symbol": "BTC/USDT"}),
        encoding="utf-8",
    )
    (crypto_directory / "run_metadata.json").write_text(
        json.dumps({"config_sha256": config_hash(config)}),
        encoding="utf-8",
    )

    output = run_crypto_walk_forward_validation(
        tmp_path / "run",
        config,
        output_directory=tmp_path / "validation",
        min_history_weeks=2,
        test_window_weeks=3,
        cost_bps_per_side=(0.0, 10.0),
        write_charts=False,
    )

    expected = {
        "event_outcomes.csv",
        "event_summary.csv",
        "fold_definitions.csv",
        "cost_sensitivity.csv",
        "config_snapshot.json",
        "validation_manifest.json",
        "validation_report.md",
    }
    assert expected.issubset({path.name for path in output.iterdir()})
    report = (output / "validation_report.md").read_text(encoding="utf-8")
    assert "Thresholds remain unchanged" in report


def test_crypto_validation_rejects_changed_configuration(tmp_path):
    crypto_directory = tmp_path / "crypto"
    crypto_directory.mkdir()
    (crypto_directory / "run_metadata.json").write_text(
        json.dumps({"config_sha256": config_hash({"baseline": True})}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        run_crypto_walk_forward_validation(
            crypto_directory,
            {"research": {"forward_return_horizons": [1]}},
            write_charts=False,
        )
