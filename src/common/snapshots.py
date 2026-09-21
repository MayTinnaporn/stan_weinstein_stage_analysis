from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from common.models import AnalysisBundle, BatchRunResult
from common.universe import UniverseSnapshot


def make_run_id(as_of: pd.Timestamp) -> str:
    """Create a sortable, filesystem-safe identifier from a UTC timestamp."""
    return as_of.strftime("%Y%m%dT%H%M%SZ")


def create_run_directory(output_root: str | Path, as_of: pd.Timestamp) -> Path:
    """Create a new versioned directory without overwriting an earlier run."""
    root = Path(output_root)
    base_name = make_run_id(as_of)
    candidate = root / base_name
    suffix = 2
    while candidate.exists():
        candidate = root / f"{base_name}-{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def _safe_symbol(symbol: str) -> str:
    return symbol.replace("/", "_").replace(":", "_")


def config_hash(config: dict[str, Any]) -> str:
    """Return the stable SHA-256 digest used in persisted run metadata."""
    payload = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_csv(df: pd.DataFrame, path: Path, *, index: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(temporary, index=index)
    temporary.replace(path)


def save_analysis_bundle(
    bundle: AnalysisBundle,
    output_root: str | Path,
    universe_name: str,
    config: dict[str, Any],
    *,
    run_directory: str | Path | None = None,
) -> Path:
    """Persist immutable raw, weekly, analysis, and event snapshots."""
    run_directory = (
        Path(run_directory)
        if run_directory is not None
        else Path(output_root) / make_run_id(bundle.as_of)
    )
    asset_directory = (
        run_directory / bundle.asset_type / _safe_symbol(bundle.symbol)
    )
    asset_directory.mkdir(parents=True, exist_ok=True)

    _write_csv(bundle.daily, asset_directory / "raw_daily.csv")
    _write_csv(bundle.weekly, asset_directory / "weekly.csv")
    _write_csv(bundle.analysis, asset_directory / "analysis.csv")

    event_columns = [
        column
        for column in bundle.analysis.columns
        if column.endswith("_Event")
        and pd.api.types.is_bool_dtype(bundle.analysis[column].dtype)
    ]
    if not event_columns:
        raise ValueError("Analysis bundle does not contain transition event columns")
    event_mask = bundle.analysis[event_columns].fillna(False).any(axis=1)
    _write_csv(bundle.analysis.loc[event_mask], asset_directory / "events.csv")

    metadata = {
        "asset_type": bundle.asset_type,
        "symbol": bundle.symbol,
        "as_of": bundle.as_of.isoformat(),
        "universe": universe_name,
        "config_sha256": config_hash(config),
        "last_complete_week": (
            bundle.weekly.index.max().isoformat() if not bundle.weekly.empty else None
        ),
    }
    (asset_directory / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return run_directory


def save_batch_run(
    result: BatchRunResult,
    universe: UniverseSnapshot,
    config: dict[str, Any],
) -> None:
    """Persist run-level universe, latest-state, signal, and failure tables."""
    run_directory = Path(result.run_directory)
    run_directory.mkdir(parents=True, exist_ok=True)

    _write_csv(result.latest_results, run_directory / "latest_results.csv", index=False)
    _write_csv(result.signals, run_directory / "signals.csv", index=False)
    _write_csv(result.failures, run_directory / "failures.csv", index=False)
    _write_csv(
        pd.DataFrame({"symbol": universe.symbols}),
        run_directory / "universe.csv",
        index=False,
    )

    metadata = {
        "universe": universe.name,
        "as_of": universe.as_of.isoformat(),
        "symbol_count": len(universe.symbols),
        "success_count": len(result.latest_results),
        "failure_count": len(result.failures),
        "signal_count": len(result.signals),
        "config_sha256": config_hash(config),
    }
    (run_directory / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (run_directory / "config_snapshot.json").write_text(
        json.dumps(config, indent=2, sort_keys=True),
        encoding="utf-8",
    )
