from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from common.models import BatchRunResult
from common.reporting import latest_analysis_record
from common.snapshots import create_run_directory, save_analysis_bundle, save_batch_run
from common.time import to_utc_timestamp
from common.universe import UniverseSnapshot
from crypto.data_loader import fetch_daily_ohlcv
from crypto.pipeline import analyze_crypto_bundle

logger = logging.getLogger(__name__)


def run_crypto_batch(
    universe: UniverseSnapshot,
    config: dict[str, Any],
    *,
    output_root: str | Path = "outputs/runs",
) -> BatchRunResult:
    """Run a reproducible multi-symbol crypto analysis snapshot."""
    as_of = to_utc_timestamp(universe.as_of)
    benchmark_symbol = config["research"]["benchmark_symbol"]
    exchange_id = config["exchange"]["id"]
    start = config["data"]["start"]
    end = (as_of.normalize() - pd.Timedelta(days=1)).date().isoformat()
    run_root = create_run_directory(output_root, as_of)
    run_directory = run_root / "crypto"

    benchmark_daily = fetch_daily_ohlcv(
        benchmark_symbol,
        start,
        end=end,
        exchange_id=exchange_id,
    )

    latest_records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for symbol in universe.symbols:
        try:
            bundle = analyze_crypto_bundle(
                symbol,
                config,
                as_of=as_of,
                target_daily=benchmark_daily if symbol == benchmark_symbol else None,
                benchmark_daily=benchmark_daily,
            )
            save_analysis_bundle(
                bundle,
                output_root,
                universe.name,
                config,
                run_directory=run_root,
            )
            latest_records.append(latest_analysis_record(bundle))
        except Exception as exc:  # continue the universe and persist the failure
            logger.exception("Crypto batch failed for %s", symbol)
            failures.append({"Symbol": symbol, "Error": str(exc)})

    latest = pd.DataFrame(latest_records)
    if latest.empty:
        signals = latest.copy()
    else:
        signal_mask = latest[["Stage2A_Event", "Stage4A_Event"]].fillna(False).any(axis=1)
        signals = latest.loc[signal_mask].copy()

    result = BatchRunResult(
        str(run_directory),
        latest,
        signals,
        pd.DataFrame(failures, columns=["Symbol", "Error"]),
    )
    save_batch_run(result, universe, config)
    return result
