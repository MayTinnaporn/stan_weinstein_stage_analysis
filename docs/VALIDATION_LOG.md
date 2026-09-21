# Validation Log

This log records visual and mechanical validation before any classifier
thresholds are tuned.

## 2026-09-21 — Crypto V0 baseline

- As-of timestamp: `2026-09-21T01:00:00Z`
- Data source: Binance through CCXT
- Completed week cutoff: Sunday 2026-09-20
- Assets: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT
- Configuration: unchanged from `config/crypto.yaml`
- Batch result: four successes, zero failures

| Asset | Weeks | Stage 2A candidates | Stage 2A events | Stage 4A candidates | Stage 4A events |
|---|---:|---:|---:|---:|---:|
| BTC/USDT | 350 | 16 | 9 | 6 | 4 |
| ETH/USDT | 350 | 5 | 3 | 7 | 5 |
| SOL/USDT | 318 | 10 | 8 | 9 | 7 |
| XRP/USDT | 350 | 8 | 5 | 3 | 3 |

### Initial observations

- Support and resistance levels use only prior weeks and visually step forward
  without using the current candle.
- Stage 2 broadly aligns with sustained advances and Stage 4 with sustained
  declines in the four charts.
- Candidate flags sometimes persist across adjacent weeks. Rising-edge event
  columns correctly reduce these to one notification event per candidate run.
- Stage 1 and Stage 3 switch frequently during choppy regions. This is the main
  area to evaluate with forward-return evidence before changing thresholds.
- The current full-history linear-scale chart compresses early price action.
  A log-scale or zoomed-window option would improve later manual review, but no
  classifier parameter was changed during this pass.

This is an initial visual pass, not final model approval. The next validation
step is transition-level forward-return analysis and walk-forward testing.
