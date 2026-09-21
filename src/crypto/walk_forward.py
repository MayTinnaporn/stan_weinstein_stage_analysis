from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from common.backtest import backtest_long_transitions, summarize_trades
from common.snapshots import config_hash
from common.walk_forward import (
    build_walk_forward_folds,
    calculate_walk_forward_event_outcomes,
    summarize_walk_forward_outcomes,
)


def _resolve_crypto_directory(run_directory: str | Path) -> Path:
    candidate = Path(run_directory)
    crypto_directory = candidate / "crypto" if (candidate / "crypto").is_dir() else candidate
    if not crypto_directory.is_dir():
        raise ValueError(f"Crypto run directory does not exist: {crypto_directory}")
    return crypto_directory


def _read_analysis(path: Path) -> pd.DataFrame:
    analysis = pd.read_csv(path, index_col=0, parse_dates=True)
    analysis.index = pd.to_datetime(analysis.index, utc=True)
    return analysis.sort_index()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _symbol_from_analysis_path(path: Path) -> str:
    metadata_path = path.parent / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return str(metadata["symbol"])
    return path.parent.name.replace("_", "/", 1)


def _validate_config(crypto_directory: Path, config: dict[str, Any]) -> str:
    actual_hash = config_hash(config)
    metadata_path = crypto_directory / "run_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected_hash = metadata.get("config_sha256")
        if expected_hash and expected_hash != actual_hash:
            raise ValueError(
                "The supplied configuration does not match the batch run: "
                f"expected {expected_hash}, received {actual_hash}"
            )
    return actual_hash


def _plot_transition_windows(
    analysis: pd.DataFrame,
    *,
    symbol: str,
    output_directory: Path,
    min_history_weeks: int,
    window_weeks: int,
) -> int:
    output_directory.mkdir(parents=True, exist_ok=True)
    event_columns = ("Stage2A_Event", "Stage4A_Event")
    event_count = 0

    for event_column in event_columns:
        mask = analysis[event_column].fillna(False).astype(bool)
        for position in [analysis.index.get_loc(index) for index in analysis.index[mask]]:
            if position < min_history_weeks:
                continue
            start = max(0, position - window_weeks)
            end = min(len(analysis), position + window_weeks + 1)
            window = analysis.iloc[start:end]
            event_week = analysis.index[position]

            fig, ax = plt.subplots(figsize=(11, 5))
            ax.plot(window.index, window["Close"], label="Weekly Close", linewidth=1.8)
            if "MA30" in window.columns:
                ax.plot(window.index, window["MA30"], label="30W SMA", linewidth=1.2)
            for column, label in (
                ("Resistance_26w", "26W Resistance"),
                ("Support_26w", "26W Support"),
            ):
                if column in window.columns:
                    ax.plot(window.index, window[column], label=label, linestyle="--")

            color = "green" if event_column == "Stage2A_Event" else "red"
            ax.axvline(event_week, color=color, linestyle=":", linewidth=2)
            ax.scatter(
                [event_week],
                [analysis["Close"].iloc[position]],
                color=color,
                s=70,
                zorder=5,
                label=event_column,
            )
            ax.set_title(f"{symbol} {event_column} — {event_week.date()}")
            ax.set_xlabel("Completed week")
            ax.set_ylabel("Price")
            ax.grid(True, alpha=0.25)
            ax.legend(loc="best")
            fig.tight_layout()

            safe_symbol = symbol.replace("/", "_").replace(":", "_")
            output_path = output_directory / (
                f"{safe_symbol}_{event_column}_{event_week.date().isoformat()}.png"
            )
            fig.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            event_count += 1
    return event_count


def _markdown_summary_table(summary: pd.DataFrame) -> list[str]:
    aggregate = summary.loc[
        (summary["Symbol"] == "ALL_SYMBOLS") & (summary["Fold"] == "ALL")
    ]
    lines = [
        "| Event | Horizon | Count | Censored | Median return | Directional success | Median MFE | Median MAE |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def format_percent(value: float) -> str:
        return "—" if pd.isna(value) else f"{value:.1%}"

    for row in aggregate.itertuples(index=False):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.Event),
                    f"{row.HorizonWeeks}w",
                    str(row.Count),
                    str(row.CensoredCount),
                    format_percent(row.MedianReturn),
                    format_percent(row.DirectionalSuccessProbability),
                    format_percent(row.MedianMFE),
                    format_percent(row.MedianMAE),
                ]
            )
            + " |"
        )
    return lines


def _write_report(
    output_path: Path,
    *,
    source_directory: Path,
    as_of: str,
    config_sha256: str,
    symbols: list[str],
    horizons: tuple[int, ...],
    min_history_weeks: int,
    test_window_weeks: int,
    chart_count: int,
    summary: pd.DataFrame,
) -> None:
    lines = [
        "# Crypto Walk-Forward Baseline Report",
        "",
        "This report evaluates the frozen classifier chronologically. It does not fit",
        "or tune parameters inside any fold. Outcomes use only bars after each event;",
        "unelapsed horizons are retained as censored observations.",
        "",
        "## Run definition",
        "",
        f"- Source batch: `{source_directory}`",
        f"- As of: `{as_of}`",
        f"- Configuration SHA-256: `{config_sha256}`",
        f"- Symbols: {', '.join(symbols)}",
        f"- Initial history: {min_history_weeks} weeks",
        f"- Test block: {test_window_weeks} weeks",
        f"- Forward horizons: {', '.join(f'{value}w' for value in horizons)}",
        f"- Transition charts: {chart_count}",
        "",
        "## Aggregate transition outcomes",
        "",
        "Directional success means a positive return after Stage 2A and a negative",
        "return after Stage 4A.",
        "",
        *_markdown_summary_table(summary),
        "",
        "## Interpretation guardrails",
        "",
        "- Small event counts are descriptive evidence, not proof of an edge.",
        "- Overlapping forward horizons make observations statistically dependent.",
        "- Results apply to the persisted symbols and venue data, not the future top-40 universe.",
        "- Transaction-cost results are a sensitivity check, not a portfolio backtest.",
        "- Thresholds remain unchanged in this baseline report.",
        "",
        "Inspect `event_outcomes.csv`, `event_summary.csv`, `cost_sensitivity.csv`,",
        "`fold_definitions.csv`, and the `transition_charts/` directory before drawing",
        "a model decision.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_crypto_walk_forward_validation(
    run_directory: str | Path,
    config: dict[str, Any],
    *,
    output_directory: str | Path | None = None,
    min_history_weeks: int = 104,
    test_window_weeks: int = 52,
    cost_bps_per_side: tuple[float, ...] = (0.0, 10.0, 25.0),
    chart_window_weeks: int = 13,
    write_charts: bool = True,
) -> Path:
    """Validate persisted crypto analyses with frozen chronological test blocks."""
    crypto_directory = _resolve_crypto_directory(run_directory)
    output_path = (
        Path(output_directory)
        if output_directory is not None
        else crypto_directory / "walk_forward_validation"
    )
    output_path.mkdir(parents=True, exist_ok=True)

    config_sha256 = _validate_config(crypto_directory, config)
    run_metadata_path = crypto_directory / "run_metadata.json"
    source_run_metadata = (
        json.loads(run_metadata_path.read_text(encoding="utf-8"))
        if run_metadata_path.exists()
        else {}
    )
    horizons = tuple(int(value) for value in config["research"]["forward_return_horizons"])
    analysis_paths = sorted(crypto_directory.glob("*/analysis.csv"))
    if not analysis_paths:
        raise ValueError(f"No crypto analysis files found under {crypto_directory}")

    outcome_tables: list[pd.DataFrame] = []
    fold_tables: list[pd.DataFrame] = []
    cost_rows: list[dict[str, Any]] = []
    input_files: list[dict[str, str]] = []
    symbols: list[str] = []
    chart_count = 0

    for analysis_path in analysis_paths:
        symbol = _symbol_from_analysis_path(analysis_path)
        symbols.append(symbol)
        analysis = _read_analysis(analysis_path)
        input_files.append(
            {"path": str(analysis_path), "sha256": _file_sha256(analysis_path)}
        )
        fold_tables.append(
            build_walk_forward_folds(
                analysis,
                symbol=symbol,
                min_history_weeks=min_history_weeks,
                test_window_weeks=test_window_weeks,
            )
        )
        outcome_tables.append(
            calculate_walk_forward_event_outcomes(
                analysis,
                symbol=symbol,
                horizons=horizons,
                min_history_weeks=min_history_weeks,
                test_window_weeks=test_window_weeks,
            )
        )

        evaluation_data = analysis.iloc[min_history_weeks:].copy()
        for cost_bps in cost_bps_per_side:
            trades = backtest_long_transitions(
                evaluation_data,
                transaction_cost_bps_per_side=float(cost_bps),
            )
            trade_summary = summarize_trades(trades)
            cost_rows.append(
                {
                    "Symbol": symbol,
                    "CostBpsPerSide": float(cost_bps),
                    **trade_summary.to_dict(),
                }
            )

        if write_charts:
            chart_count += _plot_transition_windows(
                analysis,
                symbol=symbol,
                output_directory=output_path / "transition_charts",
                min_history_weeks=min_history_weeks,
                window_weeks=chart_window_weeks,
            )

    outcomes = pd.concat(outcome_tables, ignore_index=True)
    summary = summarize_walk_forward_outcomes(outcomes)
    if not outcomes.empty:
        pooled_outcomes = outcomes.copy()
        pooled_outcomes["Symbol"] = "ALL_SYMBOLS"
        summary = pd.concat(
            [summary, summarize_walk_forward_outcomes(pooled_outcomes)],
            ignore_index=True,
        )
    folds = pd.concat(fold_tables, ignore_index=True)
    cost_sensitivity = pd.DataFrame(cost_rows)

    outcomes.to_csv(output_path / "event_outcomes.csv", index=False)
    summary.to_csv(output_path / "event_summary.csv", index=False)
    folds.to_csv(output_path / "fold_definitions.csv", index=False)
    cost_sensitivity.to_csv(output_path / "cost_sensitivity.csv", index=False)
    (output_path / "config_snapshot.json").write_text(
        json.dumps(config, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest = {
        "source_directory": str(crypto_directory),
        "source_run_metadata": source_run_metadata,
        "configuration_sha256": config_sha256,
        "symbols": symbols,
        "horizons": horizons,
        "min_history_weeks": min_history_weeks,
        "test_window_weeks": test_window_weeks,
        "cost_bps_per_side": cost_bps_per_side,
        "chart_window_weeks": chart_window_weeks,
        "transition_chart_count": chart_count,
        "input_files": input_files,
    }
    (output_path / "validation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_report(
        output_path / "validation_report.md",
        source_directory=crypto_directory,
        as_of=str(source_run_metadata.get("as_of", "unknown")),
        config_sha256=config_sha256,
        symbols=symbols,
        horizons=horizons,
        min_history_weeks=min_history_weeks,
        test_window_weeks=test_window_weeks,
        chart_count=chart_count,
        summary=summary,
    )
    return output_path
