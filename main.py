from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from common.backtest import backtest_long_transitions, summarize_trades
from common.config import load_yaml_config
from common.time import to_utc_timestamp
from common.universe import CsvPointInTimeUniverseProvider, StaticUniverseProvider
from crypto.batch import run_crypto_batch
from crypto.pipeline import analyze_crypto
from crypto.validation import (
    summarize_event_forward_returns as summarize_crypto_events,
)
from crypto.validation import summarize_forward_returns as summarize_crypto_returns
from crypto.visualization import plot_stage_analysis as plot_crypto_stage
from crypto.walk_forward import run_crypto_walk_forward_validation
from stocks.batch import run_stock_batch
from stocks.pipeline import analyze_stock
from stocks.validation import (
    summarize_event_forward_returns as summarize_stock_events,
)
from stocks.validation import summarize_forward_returns as summarize_stock_returns
from stocks.visualization import plot_stage_analysis as plot_stock_stage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Market Stage Analysis V0."
    )

    subparsers = parser.add_subparsers(dest="asset_type", required=True)

    crypto_parser = subparsers.add_parser("crypto")
    crypto_parser.add_argument("--symbol", default="BTC/USDT")
    crypto_parser.add_argument(
        "--config",
        default="config/crypto.yaml",
    )
    crypto_parser.add_argument("--as-of", default=None)

    stock_parser = subparsers.add_parser("stock")
    stock_parser.add_argument("--symbol", default="AAPL")
    stock_parser.add_argument(
        "--sector",
        default=None,
        help="Optional sector benchmark, e.g. SMH or XLK",
    )
    stock_parser.add_argument(
        "--config",
        default="config/stocks.yaml",
    )
    stock_parser.add_argument("--as-of", default=None)

    for command, default_config in (
        ("crypto-batch", "config/crypto.yaml"),
        ("stock-batch", "config/stocks.yaml"),
    ):
        batch_parser = subparsers.add_parser(command)
        batch_parser.add_argument("--config", default=default_config)
        batch_parser.add_argument("--as-of", default=None)
        batch_parser.add_argument("--symbols", nargs="+")
        batch_parser.add_argument("--universe-csv")
        batch_parser.add_argument("--universe-name", default=f"{command}-research")
        batch_parser.add_argument("--output-root", default="outputs/runs")

    backtest_parser = subparsers.add_parser("backtest")
    backtest_parser.add_argument("--input", required=True)
    backtest_parser.add_argument("--output-dir", default=None)
    backtest_parser.add_argument("--cost-bps-per-side", type=float, default=0.0)
    backtest_parser.add_argument("--entry-column", default="Stage2A_Event")
    backtest_parser.add_argument("--exit-column", default="Stage4A_Event")

    validation_parser = subparsers.add_parser("crypto-validate")
    validation_parser.add_argument("--run-dir", required=True)
    validation_parser.add_argument("--config", default="config/crypto.yaml")
    validation_parser.add_argument("--output-dir", default=None)
    validation_parser.add_argument("--min-history-weeks", type=int, default=104)
    validation_parser.add_argument("--test-window-weeks", type=int, default=52)
    validation_parser.add_argument(
        "--cost-bps-per-side",
        type=float,
        nargs="+",
        default=[0.0, 10.0, 25.0],
    )
    validation_parser.add_argument("--chart-window-weeks", type=int, default=13)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if args.asset_type == "backtest":
        input_path = Path(args.input)
        weekly = pd.read_csv(input_path, index_col=0, parse_dates=True)
        trades = backtest_long_transitions(
            weekly,
            entry_column=args.entry_column,
            exit_column=args.exit_column,
            transaction_cost_bps_per_side=args.cost_bps_per_side,
        )
        summary = summarize_trades(trades)
        output_dir = Path(args.output_dir) if args.output_dir else input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        trades_path = output_dir / "backtest_trades.csv"
        summary_path = output_dir / "backtest_summary.csv"
        trades.to_csv(trades_path, index=False)
        summary.rename("Value").to_csv(summary_path, header=True)
        print(f"Saved: {trades_path}")
        print(f"Saved: {summary_path}")
        return

    if args.asset_type == "crypto-validate":
        config = load_yaml_config(args.config)
        validation_directory = run_crypto_walk_forward_validation(
            args.run_dir,
            config,
            output_directory=args.output_dir,
            min_history_weeks=args.min_history_weeks,
            test_window_weeks=args.test_window_weeks,
            cost_bps_per_side=tuple(args.cost_bps_per_side),
            chart_window_weeks=args.chart_window_weeks,
        )
        print(f"Saved crypto walk-forward validation: {validation_directory}")
        return

    if args.asset_type in {"crypto-batch", "stock-batch"}:
        config = load_yaml_config(args.config)
        as_of = to_utc_timestamp(args.as_of)
        if args.universe_csv:
            provider = CsvPointInTimeUniverseProvider(
                args.universe_name,
                args.universe_csv,
            )
        else:
            symbols = args.symbols or config["research"]["initial_symbols"]
            provider = StaticUniverseProvider(args.universe_name, tuple(symbols))
        universe = provider.snapshot(as_of)

        if args.asset_type == "crypto-batch":
            batch_result = run_crypto_batch(
                universe,
                config,
                output_root=args.output_root,
            )
        else:
            batch_result = run_stock_batch(
                universe,
                config,
                output_root=args.output_root,
            )

        print(f"Saved batch run: {batch_result.run_directory}")
        print(f"Successful symbols: {len(batch_result.latest_results)}")
        print(f"New signals: {len(batch_result.signals)}")
        print(f"Failures: {len(batch_result.failures)}")
        return

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.asset_type == "crypto":
        config = load_yaml_config(args.config)
        result = analyze_crypto(args.symbol, config, as_of=args.as_of)

        safe_symbol = args.symbol.replace("/", "_")
        csv_path = output_dir / f"{safe_symbol}_crypto_weekly_stage_analysis.csv"
        png_path = output_dir / f"{safe_symbol}_crypto_stage_chart.png"
        summary_path = output_dir / f"{safe_symbol}_crypto_forward_return_summary.csv"
        event_summary_path = output_dir / f"{safe_symbol}_crypto_event_summary.csv"

        result.to_csv(csv_path)
        plot_crypto_stage(result, args.symbol, png_path)

        summary = summarize_crypto_returns(
            result,
            horizons=config["research"]["forward_return_horizons"],
        )
        summary.to_csv(summary_path, index=False)
        event_summary = pd.concat(
            [
                summarize_crypto_events(
                    result,
                    event_column,
                    horizons=config["research"]["forward_return_horizons"],
                )
                for event_column in ("Stage2A_Event", "Stage4A_Event")
            ],
            ignore_index=True,
        )
        event_summary.to_csv(event_summary_path, index=False)

    else:
        config = load_yaml_config(args.config)
        result = analyze_stock(
            args.symbol,
            config,
            sector_symbol=args.sector,
            as_of=args.as_of,
        )

        safe_symbol = args.symbol.replace("/", "_")
        csv_path = output_dir / f"{safe_symbol}_stock_weekly_stage_analysis.csv"
        png_path = output_dir / f"{safe_symbol}_stock_stage_chart.png"
        summary_path = output_dir / f"{safe_symbol}_stock_forward_return_summary.csv"
        event_summary_path = output_dir / f"{safe_symbol}_stock_event_summary.csv"

        result.to_csv(csv_path)
        plot_stock_stage(result, args.symbol, png_path)

        summary = summarize_stock_returns(
            result,
            horizons=config["research"]["forward_return_horizons"],
        )
        summary.to_csv(summary_path, index=False)
        event_summary = pd.concat(
            [
                summarize_stock_events(
                    result,
                    event_column,
                    horizons=config["research"]["forward_return_horizons"],
                )
                for event_column in ("Stage2A_Event", "Stage4A_Event")
            ],
            ignore_index=True,
        )
        event_summary.to_csv(event_summary_path, index=False)

    print(f"Saved: {csv_path}")
    print(f"Saved: {png_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {event_summary_path}")


if __name__ == "__main__":
    main()
