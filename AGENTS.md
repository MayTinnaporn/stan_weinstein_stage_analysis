# Codex Instructions

This repository implements systematic Stan Weinstein-style Stage Analysis for cryptocurrencies and stocks.

Before making architectural or modeling decisions, read `PROJECT_BRIEF.md` and treat it as the source of truth for current research assumptions.

## Current Priority

Both V0 implementations exist, but the first active validation priority is still the cryptocurrency system.

The frozen four-asset baseline, manual transition audit, and episode-aware
comparison are complete. Read `docs/TRANSITION_AUDIT.md` and
`docs/SEMANTIC_COMPARISON.md`. The next research task is causal Stage 2A
base-quality diagnostics; do not tune numeric thresholds yet.

The long-term operating target is a Monday-morning scan of point-in-time S&P
500 constituents and the eligible top 40 cryptocurrencies, followed by
notification of newly entered Stage 2A and Stage 4A states. Notifications and
the HTML infographic are not implemented yet and must wait for validation.

Initial crypto assets:
- BTC/USDT
- ETH/USDT
- SOL/USDT
- XRP/USDT

Initial stock examples:
- AAPL
- MSFT
- NVDA
- AMZN
- JPM
- XOM
- CAT
- WMT
- KO
- TSLA

Do not optimize either system until visual validation has been completed.

## Important Research Rules

- Do not introduce look-ahead bias.
- Never calculate support/resistance using information unavailable at that historical point.
- Do not treat incomplete weekly candles as completed observations.
- Keep experimental thresholds configurable.
- Keep the current transition backtester research-only; do not turn either
  classifier into a live trading or portfolio-management system.
- Do not add anomaly detection yet.
- Do not silently change research assumptions from `PROJECT_BRIEF.md`.
- Do not assume stock and crypto parameters should match.

If an assumption is unclear, document it rather than hiding it in implementation logic.

## Architecture

Keep reusable logic separate from asset-specific logic.

```text
src/
  common/
  crypto/
  stocks/
```

Crypto and stock Stage Analysis must remain independently configurable.

## Code Style

Use Python and prefer:
- small functions
- type hints
- docstrings
- explicit names
- configuration files
- testable pure functions where practical

Use UV for Python and dependency management:
- keep dependencies in `pyproject.toml`,
- commit `uv.lock`,
- use `uv sync` to create/update the environment,
- use `uv run` for project commands,
- use `uv add` and `uv remove` instead of editing a separate requirements file.

Data-source boundaries:

- Yahoo Finance through `yfinance` supplies initial stock OHLCV.
- CoinGecko supplies point-in-time crypto market-cap rankings.
- Binance spot through CCXT supplies venue-specific crypto OHLCV.
- Historical S&P 500 and crypto tests require point-in-time membership.
- Persist resolved universes and never silently substitute data providers.

Add tests for calculations where mistakes could materially affect research conclusions.

## Validation

For each engine, verify:
1. historical data loading,
2. correct weekly aggregation,
3. feature calculations,
4. Stage 1-4 labels,
5. Stage 2A and Stage 4A candidates,
6. plotting,
7. critical unit tests,
8. forward-return validation.

For stocks, explicitly verify split/dividend adjustment behavior and benchmark alignment.
