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
from stocks.data_loader import fetch_daily_ohlcv
from stocks.pipeline import analyze_stock_bundle

logger = logging.getLogger(__name__)


def run_stock_batch(
    universe: UniverseSnapshot,
    config: dict[str, Any],
    *,
    output_root: str | Path = "outputs/runs",
    sector_by_symbol: dict[str, str] | None = None,
) -> BatchRunResult:
    """Run a reproducible multi-symbol stock analysis snapshot."""
    as_of = to_utc_timestamp(universe.as_of)
    market_symbol = config["research"]["market_benchmark"]
    start = config["data"]["start"]
    auto_adjust = bool(config["data"]["auto_adjust"])
    end = as_of.date().isoformat()
    run_root = create_run_directory(output_root, as_of)
    run_directory = run_root / "stocks"

    market_daily = fetch_daily_ohlcv(
        market_symbol,
        start,
        end=end,
        auto_adjust=auto_adjust,
    )
    sector_cache: dict[str, pd.DataFrame] = {}
    latest_records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for symbol in universe.symbols:
        try:
            sector_symbol = (sector_by_symbol or {}).get(symbol)
            sector_daily = None
            if sector_symbol and sector_symbol != symbol:
                if sector_symbol not in sector_cache:
                    sector_cache[sector_symbol] = fetch_daily_ohlcv(
                        sector_symbol,
                        start,
                        end=end,
                        auto_adjust=auto_adjust,
                    )
                sector_daily = sector_cache[sector_symbol]

            bundle = analyze_stock_bundle(
                symbol,
                config,
                as_of=as_of,
                sector_symbol=sector_symbol,
                target_daily=market_daily if symbol == market_symbol else None,
                market_daily=market_daily,
                sector_daily=sector_daily,
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
            logger.exception("Stock batch failed for %s", symbol)
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
