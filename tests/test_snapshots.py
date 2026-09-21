import json

import pandas as pd

from common.models import AnalysisBundle, BatchRunResult
from common.snapshots import create_run_directory, save_analysis_bundle, save_batch_run
from common.universe import UniverseSnapshot


def test_analysis_and_batch_snapshots_are_persisted(tmp_path):
    index = pd.date_range("2026-09-13", periods=2, freq="W-SUN", tz="UTC")
    daily_index = pd.date_range("2026-09-07", periods=14, freq="D", tz="UTC")
    daily = pd.DataFrame(
        {
            "Open": 1.0,
            "High": 2.0,
            "Low": 0.5,
            "Close": 1.5,
            "Volume": 100.0,
        },
        index=daily_index,
    )
    weekly = pd.DataFrame(
        {
            "Open": [1.0, 1.1],
            "High": [2.0, 2.1],
            "Low": [0.5, 0.6],
            "Close": [1.5, 1.6],
            "Volume": [700.0, 700.0],
        },
        index=index,
    )
    analysis = weekly.assign(
        Stage=[1.0, 2.0],
        Stage2A=[False, True],
        Stage4A=[False, False],
        Stage2A_Event=[False, True],
        Stage4A_Event=[False, False],
        Weeks_Since_Stage2A_Event=pd.Series(
            [pd.NA, 1],
            index=weekly.index,
            dtype="Int64",
        ),
    )
    as_of = pd.Timestamp("2026-09-21T01:00:00Z")
    bundle = AnalysisBundle("crypto", "BTC/USDT", as_of, daily, weekly, analysis)
    config = {"research": {"name": "test"}}

    run_directory = save_analysis_bundle(bundle, tmp_path, "test-universe", config)
    asset_directory = run_directory / "crypto" / "BTC_USDT"

    assert (asset_directory / "raw_daily.csv").exists()
    assert (asset_directory / "weekly.csv").exists()
    assert (asset_directory / "analysis.csv").exists()
    assert len(pd.read_csv(asset_directory / "events.csv")) == 1

    latest = pd.DataFrame([{"Symbol": "BTC/USDT", "Stage2A_Event": True}])
    batch_directory = run_directory / "crypto"
    result = BatchRunResult(str(batch_directory), latest, latest, pd.DataFrame())
    universe = UniverseSnapshot("test-universe", as_of, ("BTC/USDT",))
    save_batch_run(result, universe, config)

    metadata = json.loads((batch_directory / "run_metadata.json").read_text())
    assert metadata["signal_count"] == 1
    snapshot = json.loads((batch_directory / "config_snapshot.json").read_text())
    assert snapshot == config


def test_run_directories_are_versioned_instead_of_overwritten(tmp_path):
    as_of = pd.Timestamp("2026-09-21T01:00:00Z")

    first = create_run_directory(tmp_path, as_of)
    second = create_run_directory(tmp_path, as_of)

    assert first.name == "20260921T010000Z"
    assert second.name == "20260921T010000Z-02"
