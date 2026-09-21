# Stock Stage Analysis V0

This folder contains the first-pass stock research implementation.

Key stock-specific differences from crypto:

- daily data is downloaded with yfinance,
- data is adjusted for splits/dividends by default,
- weekly bars end Friday,
- market-relative Mansfield RS is supported,
- optional sector-relative Mansfield RS is supported,
- stock thresholds remain independent from crypto thresholds.

This implementation is intentionally transparent and simple so it can be visually validated before refinement.

## Data and universe policy

Yahoo Finance is accessed through `yfinance` for personal research. Adjusted
OHLCV is enabled by default so stock splits do not appear as price collapses.
Any change to adjustment behavior must be documented and covered by tests,
including dividend treatment and alignment of the stock, market benchmark, and
optional sector benchmark.

A current symbol list is acceptable for visual validation, but not for a
historical S&P 500 backtest. Historical runs require effective membership dates
through `--universe-csv`; otherwise survivorship bias would be introduced.

## Commands

```bash
uv run python main.py stock --symbol AAPL
uv run python main.py stock --symbol NVDA --sector SMH

uv run python main.py stock-batch \
  --as-of 2026-09-21T01:00:00Z \
  --universe-name sp500-history \
  --universe-csv data/sp500_membership.csv
```

The live acquisition of historical S&P 500 membership and the weekly scheduler
are not implemented yet. Batch artifacts under `outputs/runs/` include the
resolved universe, analysis data, events, failures, and run metadata.
