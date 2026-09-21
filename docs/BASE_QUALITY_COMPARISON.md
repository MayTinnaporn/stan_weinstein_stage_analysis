# Stage 2A Base-Quality Comparison

## Purpose

This experiment follows the episode-aware comparison without changing the V0
classifier or production event fields. It asks whether a Stage 2A episode is
more useful when it follows recent Stage 1 evidence, and records continuous
pre-breakout diagnostics for later hypothesis design.

Source run: `outputs/runs/20260921T010000Z-06/crypto`

Configuration SHA-256:
`4fbd9a357e4f617f177595f82313fda65ea945a053e84b68541cbb6b07e6d85a`

Assets: BTC/USDT, ETH/USDT, SOL/USDT, XRP/USDT  
Initial history: 104 weeks  
Chronological test blocks: 52 weeks  
Classifier thresholds: unchanged

## Causal definitions

All diagnostic values at week *t* use only completed information available by
week *t*. Forward returns are validation outcomes and never classifier inputs.

The predeclared binary hypothesis is:

- start with a Stage 2A episode start;
- require at least one Stage 1 label among the prior 13 completed weeks; and
- optionally assess the existing next-week confirmation one week later.

The system also persists these descriptive measurements without filtering on
them:

- Stage 1 weeks in the prior window and weeks since Stage 1;
- prior 13-week return, range width, and weekly-return volatility;
- resistance age;
- breakout-week return and distance above resistance in ATR units;
- distance above the 30-week average, volume ratio, range width, and BTC
  relative-strength slope where applicable.

## Predeclared hypothesis result

| Variant | Count | 4w median / success | 8w median / success | 13w median / success | 26w median / success |
|---|---:|---:|---:|---:|---:|
| Episode start | 12 | -2.1% / 50.0% | -8.1% / 41.7% | -12.9% / 41.7% | +12.2% / 50.0% |
| Recent Stage 1 | 11 | -5.6% / 45.5% | -12.3% / 45.5% | -20.0% / 45.5% | +29.5% / 54.5% |
| No recent Stage 1 | 1 | +8.3% / 100.0% | -3.8% / 0.0% | -5.8% / 0.0% | -5.2% / 0.0% |
| Confirmed | 10 | +6.4% / 50.0% | +2.5% / 50.0% | +7.9% / 60.0% | +6.2% / 50.0% |
| Confirmed + recent Stage 1 | 9 | +14.2% / 55.6% | +5.2% / 55.6% | +7.0% / 55.6% | +18.5% / 55.6% |

The recent-Stage-1 condition selects 11 of 12 episode starts. It therefore has
almost no discriminatory power in this sample. Differences from the episode
start result are driven by excluding one observation and cannot validate the
hypothesis. The same limitation applies to the confirmed comparison, where the
condition retains 9 of 10 events.

## Descriptive feature patterns

The table compares medians for V0 Stage 2A events with positive versus
non-positive returns. It is exploratory evidence, not a threshold search.

| Feature | Horizon | Failure median | Success median |
|---|---:|---:|---:|
| Prior base range | 4w | 46.9% | 37.1% |
| Prior base range | 8w | 45.0% | 34.7% |
| Prior base range | 13w | 45.0% | 37.1% |
| Prior volatility | 4w | 11.2% | 6.5% |
| Prior volatility | 8w | 9.9% | 6.5% |
| Prior volatility | 13w | 9.9% | 6.5% |
| Resistance age | 4w | 4.0 weeks | 2.5 weeks |
| Resistance age | 13w | 4.5 weeks | 1.5 weeks |
| Breakout distance | 4w | 0.52 ATR | 1.02 ATR |
| Breakout distance | 13w | 0.52 ATR | 1.08 ATR |

Lower prior range and volatility align with positive outcomes at 4, 8, and 13
weeks. Younger resistance and greater breakout distance align at 4 and 13
weeks. These relationships weaken or reverse at 26 weeks, and each comparison
contains only about ten events per outcome group. No cutoff is justified.

## Decision

- Reject the recent-Stage-1 binary rule as a useful discriminator in its
  current form.
- Keep the label and continuous diagnostics as experimental research columns.
- Do not change V0 thresholds, batch signal behavior, or notification fields.
- Keep next-week confirmation as the more promising Stage 2A variant, but do
  not approve it from ten observations.
- Before defining a numeric base-quality filter, visually review the 20
  annotated Stage 2A windows without using their forward outcomes and record a
  predeclared structural rubric. Test that rubric on a broader point-in-time
  universe or a held-out period.

Machine-readable evidence is under the run's `walk_forward_validation/`
directory in `stage2a_base_quality_events.csv`,
`stage2a_base_quality_feature_summary.csv`, `event_outcomes.csv`, and
`event_summary.csv`.
