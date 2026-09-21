# Codex Instructions

This repository implements systematic Stan Weinstein-style Stage Analysis for cryptocurrencies and stocks.

Before making architectural or modeling decisions, read `PROJECT_BRIEF.md` and treat it as the source of truth for current research assumptions.

## Current Priority

Both V0 implementations exist, but the first active validation priority is still the cryptocurrency system.

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
- Do not turn either Stage classifier into a trading strategy yet.
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
