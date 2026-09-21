# Codex Handoff Prompt

Read `AGENTS.md`, `PROJECT_BRIEF.md`, `docs/DATA_SOURCES.md`, and
`docs/OPERATIONS.md` before changing architecture or model assumptions.

This repository already contains separate cryptocurrency and stock V0 engines.
Do not redesign them from scratch or assume their thresholds should match.

## Implemented

- crypto and stock daily-data loaders and weekly aggregation,
- configurable feature calculation and Stage 1–4 classification,
- Stage 2A/4A candidate and rising-edge event columns,
- plotting and forward-return validation,
- reproducible as-of batch snapshots,
- static and CSV point-in-time universe providers,
- a research-only Stage 2A-entry/Stage 4A-exit backtester,
- UV project metadata and committed lockfile.

## Current priority

Validate the cryptocurrency engine first on BTC/USDT, ETH/USDT, SOL/USDT, and
XRP/USDT. Do not optimize thresholds before visual and forward-return validation.

The next implementation milestone is:

1. CoinGecko point-in-time top-40 universe acquisition,
2. explicit eligibility filtering and CoinGecko ID ↔ Binance pair mapping,
3. point-in-time S&P 500 membership acquisition,
4. walk-forward transition validation,
5. notification state and delivery after event semantics are accepted,
6. the HTML infographic after the result schema stabilizes.

Do not describe dynamic top-40 selection, S&P membership acquisition,
scheduling, notifications, or the infographic as implemented until the code and
tests exist.

## Required safeguards

- Never use incomplete weekly candles.
- Never use current-week data in historical support/resistance.
- Never project today's constituents backward in a backtest.
- Keep source provenance and resolved universes with every batch run.
- Keep the backtester research-only; do not add live execution or position sizing.
- Keep all thresholds configurable and stock/crypto settings independent.

## Development commands

```bash
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen ruff check src tests main.py
```

Use `uv add` and `uv remove` for dependency changes and commit `uv.lock`.
