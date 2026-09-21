# Weekly Operations and Delivery Roadmap

This document distinguishes the intended Monday workflow from what the
repository currently automates.

## Target Monday workflow

Run at `01:00 UTC` on Monday (`08:00 Asia/Bangkok`) by default. At that time the
Monday–Sunday crypto candle is complete, and the prior stock trading week is
also complete. A scheduler should invoke one run with a single UTC `as_of`
timestamp and a unique run identifier.

```text
point-in-time universes
        ↓
eligibility and symbol mapping
        ↓
daily OHLCV + benchmarks
        ↓
completed weekly bars
        ↓
features and Stage 1–4
        ↓
new Stage 2A/4A events
        ↓
persisted evidence
        ↓
notification (later) → HTML infographic (later)
```

### 1. Resolve universes

- Stocks: S&P 500 membership effective at `as_of`.
- Crypto: CoinGecko market-cap ranking effective at `as_of`, followed by the
  configured exclusions and venue eligibility policy until 40 assets remain.
- Persist both the source candidates and final eligible universe.

Static lists are permitted for visual validation only. Historical research must
use point-in-time membership.

### 2. Acquire market data

- Stocks: adjusted daily OHLCV from Yahoo Finance through `yfinance`.
- Crypto: Binance spot daily OHLCV through CCXT.
- Benchmarks must use the same cutoff and compatible adjustment semantics.
- Never include a partial current week.

### 3. Analyze and detect transitions

Run the independently configured stock and crypto classifiers. Notifications
should be based on `Stage2A_Event` and `Stage4A_Event`, not the raw candidate
columns, so a condition persisting for several weeks produces one event.

### 4. Persist before delivery

Each run should retain:

- `as_of`, provider, venue, symbol, and retrieval timestamps,
- source and resolved universe snapshots with exclusions,
- configuration and configuration hash,
- raw daily data and completed weekly bars,
- feature/classification output and transition events,
- per-symbol failures and data-quality reasons.

The existing batch runner writes these research artifacts under
`outputs/runs/<timestamp>/`. Notification delivery must read from a completed
persisted run rather than recomputing signals.

### 5. Notify once

Notification delivery is not implemented. Before adding it, define an
idempotency key such as `(engine, symbol, event_type, completed_week)` and store
delivery status. Retrying a run must not duplicate a notification. A Stage 2A
message is a research entry candidate and a Stage 4A message is a research exit
candidate—not financial advice or an automated order.

### 6. Build the infographic

The HTML infographic is deliberately deferred until the output schema and
candidate definitions survive validation. It should consume persisted run
artifacts and visibly show the data cutoff, universe, failures, configuration
version, and new versus continuing candidates.

## Current implementation boundary

| Capability | Status |
|---|---|
| Static/CSV universe input | Implemented |
| Reproducible as-of batch artifacts | Implemented |
| Completed-week filtering | Implemented |
| Stage 1–4 and 2A/4A events | Implemented |
| Forward-return summaries | Implemented |
| Research transition backtest | Implemented |
| Live CoinGecko top-40 provider | Pending |
| Historical S&P 500 membership feed | Pending |
| Monday scheduler | Pending |
| Notification state/delivery | Pending |
| HTML infographic | Pending |

## Manual research run

Until dynamic universe providers and scheduling are implemented, run explicit
symbols or a prepared point-in-time CSV:

```bash
uv run python main.py crypto-batch \
  --as-of 2026-09-21T01:00:00Z \
  --symbols BTC/USDT ETH/USDT SOL/USDT XRP/USDT

uv run python main.py stock-batch \
  --as-of 2026-09-21T01:00:00Z \
  --universe-name sp500-history \
  --universe-csv data/sp500_membership.csv
```

Use `--as-of` for every recorded validation run. Review `failures.csv` and the
universe snapshot before interpreting signals.

## Failure policy

Fail closed for a symbol when data is missing, stale, malformed, mapped to an
ambiguous market, or insufficient for its configured features. Record the
reason and continue other symbols. A universe-wide or benchmark failure should
mark the run incomplete and suppress all notifications.

Never silently switch exchanges, quote currencies, adjustment modes, benchmark
symbols, or universe sources.
