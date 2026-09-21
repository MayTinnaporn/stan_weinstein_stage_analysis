# Episode-Aware Transition Comparison

## Purpose

This experiment tests event meaning without changing the frozen V0 classifier
thresholds. V0 `Stage2A_Event` and `Stage4A_Event` remain intact and remain the
only events used by the current batch `signals.csv` output.

Source run: `outputs/runs/20260921T010000Z-04/crypto`

Configuration SHA-256:
`e59635966293537e9c901d1afd2d5d49e4c7a08bd3a41104ff6e564e5584f5d7`

Assets: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT  
Initial history: 104 weeks  
Chronological test blocks: 52 weeks  
Classifier thresholds: unchanged

## Parallel definitions

### V0 event

The existing rising edge of the raw Stage 2A or Stage 4A candidate condition.

### Episode start

The first V0 event after the direction has re-armed:

- Stage 2A re-arms in Stage 1 or 4, or on an opposite Stage 4A event.
- Stage 4A re-arms in Stage 2 or 3, or on an opposite Stage 2A event.

Later same-direction V0 events before another re-arm are labeled continuation
events. These re-arm states are an explicit experimental assumption, not an
accepted Weinstein rule.

### Confirmed event

Confirmation is assessed on the next completed weekly candle after an episode
start. It is recorded at that later week, so it does not introduce look-ahead:

- Stage 2A requires `Stage == 2` and a close still above the original broken
  resistance.
- Stage 4A requires `Stage == 4` and a close still below the original broken
  support.

## Event counts

| Direction | V0 | Episode starts | Confirmed | Continuations |
|---|---:|---:|---:|---:|
| Stage 2A | 20 | 12 | 10 | 8 |
| Stage 4A | 17 | 9 | 7 | 8 |

Two Stage 2A and two Stage 4A episode starts failed next-week confirmation.

## Forward comparison

Directional success means a positive return after Stage 2A and a negative
return after Stage 4A. Counts are small and overlapping; these values are
descriptive, not inferential.

| Direction | Variant | 4w median / success | 8w median / success | 13w median / success | 26w median / success |
|---|---|---:|---:|---:|---:|
| 2A | V0 | -1.2% / 50.0% | -3.1% / 40.0% | +0.8% / 50.0% | +9.5% / 55.0% |
| 2A | Episode start | -2.1% / 50.0% | -8.1% / 41.7% | -12.9% / 41.7% | +12.2% / 50.0% |
| 2A | Confirmed | +6.4% / 50.0% | +2.5% / 50.0% | +7.9% / 60.0% | +6.2% / 50.0% |
| 2A | Continuation | -1.2% / 50.0% | -1.5% / 37.5% | +15.2% / 62.5% | +9.5% / 62.5% |
| 4A | V0 | +1.8% / 47.1% | +7.3% / 43.8% | +24.2% / 33.3% | -12.0% / 53.8% |
| 4A | Episode start | -15.2% / 66.7% | -14.2% / 66.7% | -3.9% / 50.0% | -23.9% / 71.4% |
| 4A | Confirmed | -15.3% / 85.7% | -5.9% / 71.4% | +10.9% / 42.9% | -13.4% / 83.3% |
| 4A | Continuation | +9.5% / 25.0% | +10.7% / 14.3% | +60.2% / 14.3% | +61.8% / 33.3% |

## Interpretation

### Stage 4A: event semantics materially help

The episode split isolates the behavior seen in the manual audit. First 4A
events have negative median returns at every horizon, while continuation events
have positive median returns at every horizon and very poor directional success.
Next-week confirmation is strongest at 4 and 8 weeks, though the small sample
and 13-week rebounds remain important cautions.

Research implication: Stage 4A continuation events should not be treated as new
exit notifications. Episode start and confirmed Stage 4A deserve further
out-of-sample testing as separate exit-candidate definitions.

### Stage 2A: episode gating is insufficient

Stage 2A episode starts are worse than V0 at 4–13 weeks. Continuations include
several legitimate advances, so suppressing every continuation would discard
useful evidence. Next-week confirmation improves median returns, but only 5 of
10 confirmed events are positive at 4 and 8 weeks and 6 of 10 at 13 weeks.

Research implication: do not promote the current Stage 2A episode rule. The
next hypothesis should measure base quality and distinguish a fresh range
resolution from a late momentum spike. Useful causal diagnostics include base
duration, resistance age, weeks since Stage 1, prior advance, and breakout
distance in ATR units.

### Backtest remains non-decisive

The V0 and confirmed-transition backtests still produce zero to two completed
trades per asset with very long holding periods. They cannot support a strategy
decision or meaningful transaction-cost comparison.

## Decision

- Preserve V0 columns for comparability.
- Keep all new semantic columns experimental and out of production alerts.
- Carry Stage 4A episode start, confirmation, and continuation forward as
  separate research labels.
- Do not accept the current Stage 2A episode rule.
- Test causal base-quality diagnostics for Stage 2A before expanding the crypto
  universe or changing thresholds.

That base-quality experiment is complete. See
`docs/BASE_QUALITY_COMPARISON.md`; the recent-Stage-1 binary rule was not
selective enough to accept.
