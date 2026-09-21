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
- a frozen-rule crypto walk-forward validation report with transition charts,
- UV project metadata and committed lockfile.

## Current priority

The frozen cryptocurrency baseline on BTC/USDT, ETH/USDT, SOL/USDT, and
XRP/USDT has completed visual and forward-return review. Read
`docs/TRANSITION_AUDIT.md` before changing event semantics. Do not optimize
numeric thresholds yet.

The next implementation milestone is:

1. explicit market-stage episode identity and re-arm semantics,
2. diagnostic transition charts with volume, extension, Stage, and RS evidence,
3. a frozen four-asset comparison of candidate, confirmed, and continuation events,
4. CoinGecko point-in-time top-40 acquisition and symbol mapping,
5. point-in-time S&P 500 membership acquisition,
6. notification state and delivery after event semantics are accepted,
7. the HTML infographic after the result schema stabilizes.

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
