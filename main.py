from __future__ import annotations

import argparse
import logging
from pathlib import Path

from common.config import load_yaml_config
from crypto.pipeline import analyze_crypto
from crypto.validation import summarize_forward_returns as summarize_crypto_returns
from crypto.visualization import plot_stage_analysis as plot_crypto_stage
from stocks.pipeline import analyze_stock
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

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.asset_type == "crypto":
        config = load_yaml_config(args.config)
        result = analyze_crypto(args.symbol, config)

        safe_symbol = args.symbol.replace("/", "_")
        csv_path = output_dir / f"{safe_symbol}_crypto_weekly_stage_analysis.csv"
        png_path = output_dir / f"{safe_symbol}_crypto_stage_chart.png"
        summary_path = output_dir / f"{safe_symbol}_crypto_forward_return_summary.csv"

        result.to_csv(csv_path)
        plot_crypto_stage(result, args.symbol, png_path)

        summary = summarize_crypto_returns(
            result,
            horizons=config["research"]["forward_return_horizons"],
        )
        summary.to_csv(summary_path, index=False)

    else:
        config = load_yaml_config(args.config)
        result = analyze_stock(
            args.symbol,
            config,
            sector_symbol=args.sector,
        )

        safe_symbol = args.symbol.replace("/", "_")
        csv_path = output_dir / f"{safe_symbol}_stock_weekly_stage_analysis.csv"
        png_path = output_dir / f"{safe_symbol}_stock_stage_chart.png"
        summary_path = output_dir / f"{safe_symbol}_stock_forward_return_summary.csv"

        result.to_csv(csv_path)
        plot_stock_stage(result, args.symbol, png_path)

        summary = summarize_stock_returns(
            result,
            horizons=config["research"]["forward_return_horizons"],
        )
        summary.to_csv(summary_path, index=False)

    print(f"Saved: {csv_path}")
    print(f"Saved: {png_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()
