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

## 2026-09-21 — Frozen-rule crypto walk-forward baseline

- Source run: `outputs/runs/20260921T010000Z-02/crypto`
- Configuration SHA-256:
  `68d354e5f5e20dc20f72bb4144fcde089248c141f3a88cb2e7bec62a9b93b15f`
- Initial history: 104 weeks
- Chronological test-block size: 52 weeks
- Assets: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT
- Batch result: four successes, zero failures
- Transition windows generated: 37
- Classifier thresholds: unchanged

Directional success means a positive forward return after Stage 2A and a
negative forward return after Stage 4A.

| Event | Horizon | Complete | Censored | Median return | Directional success |
|---|---:|---:|---:|---:|---:|
| Stage 2A | 4 weeks | 20 | 0 | -1.2% | 50.0% |
| Stage 2A | 8 weeks | 20 | 0 | -3.1% | 40.0% |
| Stage 2A | 13 weeks | 20 | 0 | 0.8% | 50.0% |
| Stage 2A | 26 weeks | 20 | 0 | 9.5% | 55.0% |
| Stage 4A | 4 weeks | 17 | 0 | 1.8% | 47.1% |
| Stage 4A | 8 weeks | 16 | 1 | 7.3% | 43.8% |
| Stage 4A | 13 weeks | 15 | 2 | 24.2% | 33.3% |
| Stage 4A | 26 weeks | 13 | 4 | -12.0% | 53.8% |

### Baseline interpretation

- Stage 2A does not show a convincing short-horizon advantage in this small
  sample. Its median return is negative at 4 and 8 weeks and only modestly
  positive at 13 weeks.
- The 26-week Stage 2A result is more favorable, but 20 overlapping events are
  too few and too dependent to establish an edge.
- Stage 4A does not behave consistently as a timely exit condition. Median
  returns remain positive at 4, 8, and 13 weeks; only the 26-week horizon has a
  negative median, with four outcomes still censored.
- The transition backtest produces only one or two closed trades per asset,
  with holding periods of 55–154 weeks. It is therefore not yet a useful basis
  for strategy conclusions or cost optimization.

The baseline does not justify threshold optimization. The next research step is
to inspect the 37 transition windows, identify repeatable classification failure
modes, and define any hypothesis change before testing a broader point-in-time
universe.

That review is complete. See `docs/TRANSITION_AUDIT.md` for the all-event table,
failure-mode taxonomy, and prioritized hypotheses. No classifier thresholds
were changed during the audit.
