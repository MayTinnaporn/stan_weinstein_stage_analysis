# Crypto Transition Audit — Frozen V0 Baseline

## Scope

This audit reviews all 37 Stage 2A/4A transition charts generated from the
2026-09-21 frozen baseline for BTC/USDT, ETH/USDT, SOL/USDT, and XRP/USDT.
Classifier thresholds were not changed.

The review combines:

- the 13-week chart window before and after each event,
- 4, 8, 13, and 26-week forward returns,
- event-week moving-average distance, slope, volume, momentum, and relative
  strength where available,
- the sequence of earlier events for the same asset and event type.

The visual labels below are diagnostic descriptions, not new classifier labels.

## Executive finding

The primary weakness is event semantics, not evidence for one obvious numeric
threshold change.

- Only 5 of 20 Stage 2A events look like clean, sustained breakouts from a
  distinct base. Five more are continuation/re-trigger events inside an
  existing advance, and 10 are failed, late, or single-spike breakouts.
- Only 6 of 17 Stage 4A events are clearly confirmed breakdowns. Two work at
  short horizons before reversing, and 9 are late/exhaustion breakdowns or
  failed breaks near a low.
- Fourteen of 37 events occur within 16 weeks of an earlier same-type event in
  the same asset. A one-week rising edge prevents consecutive duplicates but
  does not define a new market-stage episode.
- The 37 asset-events occur in only 25 distinct calendar weeks. Several are
  synchronized across assets, so the effective independent sample is smaller
  than the raw event count.
- Three Stage 2A events occur while the V0 stage label is Stage 3 because the
  Stage 2A rule accepts any positive MA slope while Stage 2 requires slope above
  `0.01`. One succeeds and two fail, so simply forcing label agreement is not
  yet justified—but the semantic inconsistency must be resolved.

## Recurring patterns

### 1. Re-triggering inside one trend episode

The current rising-edge logic fires again whenever a candidate turns false and
later true. It does not require a completed base, top, or opposite-stage reset.
This creates clusters such as:

- BTC Stage 2A on 2023-10-29, 2023-12-10, and 2024-03-03,
- SOL Stage 2A on 2023-10-29, 2023-12-10, 2023-12-24, and 2024-03-17,
- ETH Stage 4A on 2025-03-09 and 2025-04-06,
- XRP Stage 4A on 2026-06-28 and 2026-08-16.

These are not equivalent observations. Later events often describe trend
continuation or exhaustion, rather than a fresh Stage 1→2 or Stage 3→4
transition.

### 2. Stage 4A often detects capitulation rather than an early decline

Several Stage 4A events occur after price is already far below a falling MA and
after a large 26-week loss. The new 26-week low then arrives near the end of the
decline and is followed by a sharp rebound. The clearest cases are:

- BTC 2022-11-13,
- SOL 2022-11-13 and 2023-01-01,
- ETH 2025-04-06,
- XRP 2026-08-16.

This explains why Stage 4A has positive median returns at 4–13 weeks even
though some early breakdowns work well.

### 3. Stage 2A mixes base breakouts with late momentum spikes

The same rule identifies both clean range resolution and one-week price/volume
spikes after an asset is already extended. Examples of failed spike or late
signals include XRP 2023-07-16, ETH 2024-12-08, SOL 2024-03-17, and XRP
2025-01-19.

A simple higher volume threshold is not supported by this sample. Median event
volume is slightly lower for 13-week Stage 2A successes than failures. Likewise,
8-week Stage 4A success and failure groups have almost identical median volume.

### 4. Cross-asset events are strongly clustered

The May–June 2022 Stage 4A events and the late-2023/late-2024 Stage 2A events
occur across several assets in the same market regime. Treating each asset-event
as independent would overstate the evidence. Future inference should use
calendar-block or market-episode resampling.

## Complete event review

`13w` is the close-to-close forward return. A dash means the horizon had not
elapsed by the analysis cutoff.

| Asset | Event week | Type | 13w | Visual assessment |
|---|---|---|---:|---|
| BTC | 2023-03-19 | 2A | -5.8% | Failed breakout; initial jump did not hold above the new range |
| BTC | 2023-10-29 | 2A | +21.7% | Clean base breakout with sustained follow-through |
| BTC | 2023-12-10 | 2A | +57.5% | Continuation re-trigger; delayed follow-through after consolidation |
| BTC | 2024-03-03 | 2A | +7.4% | Extended continuation; stalled and was negative by 26 weeks |
| BTC | 2024-11-10 | 2A | +20.0% | Clean breakout with immediate follow-through |
| BTC | 2024-12-08 | 2A | -20.2% | Late re-trigger near a local high; failed at intermediate horizons |
| ETH | 2024-01-14 | 2A | +27.6% | Base breakout with pullback, then sustained advance |
| ETH | 2024-02-25 | 2A | +22.9% | Continuation re-trigger; positive intermediate result, weak 26-week result |
| ETH | 2024-12-08 | 2A | -49.5% | Exhaustion breakout at a local high followed by persistent decline |
| SOL | 2023-07-16 | 2A | -20.0% | One-week spike failed; 26-week gain came from a later, separate advance |
| SOL | 2023-10-29 | 2A | +192.4% | Clean base breakout with exceptional follow-through |
| SOL | 2023-12-10 | 2A | +92.9% | Successful continuation re-trigger inside the same advance |
| SOL | 2023-12-24 | 2A | +63.5% | Extended re-trigger; immediate drawdown but later continuation |
| SOL | 2024-03-17 | 2A | -25.0% | Late acceleration/blow-off event followed by reversal |
| SOL | 2024-11-17 | 2A | -20.7% | Volatile breakout/retest that did not establish a new trend |
| SOL | 2025-09-14 | 2A | -46.0% | Weak-slope breakout in a deteriorating structure; persistent failure |
| XRP | 2023-07-16 | 2A | -34.7% | Single-week spike above resistance followed by full retracement |
| XRP | 2024-11-17 | 2A | +158.8% | Clean base breakout with immediate sustained advance |
| XRP | 2025-01-19 | 2A | -29.7% | Late re-trigger after a large advance; momentum exhaustion |
| XRP | 2025-07-20 | 2A | -30.8% | Range breakout near a local high that failed to follow through |
| BTC | 2022-05-15 | 4A | -22.4% | Confirmed early breakdown with continued downside |
| BTC | 2022-06-12 | 4A | -17.9% | Continuation re-trigger; still followed by further decline |
| BTC | 2022-11-13 | 4A | +33.4% | Capitulation/exhaustion break near the cycle low |
| BTC | 2026-02-01 | 4A | +2.1% | Confirmed short-term breakdown with partial rebound by 13 weeks |
| ETH | 2022-05-15 | 4A | -9.8% | Confirmed breakdown; severe downside occurred inside the horizon |
| ETH | 2022-06-12 | 4A | +23.1% | Continuation re-trigger; short decline followed by rebound |
| ETH | 2025-03-09 | 4A | +24.2% | Worked for 4–8 weeks, then reversed sharply |
| ETH | 2025-04-06 | 4A | +62.6% | Re-trigger at an exhausted low; immediate failure and reversal |
| ETH | 2026-06-07 | 4A | +48.7% | Failed breakdown from an already prolonged decline |
| SOL | 2022-11-13 | 4A | +63.1% | Capitulation event after a crash; rebound dominated the outcome |
| SOL | 2023-01-01 | 4A | +105.4% | Re-trigger at the terminal low; immediate reversal |
| SOL | 2025-04-06 | 4A | +43.4% | Late breakdown after a large decline; reversed quickly |
| SOL | 2026-02-01 | 4A | -16.7% | Confirmed breakdown with persistent downside |
| SOL | 2026-06-07 | 4A | +60.2% | Failed range breakdown followed by recovery |
| XRP | 2022-05-15 | 4A | -16.2% | Confirmed breakdown with continued downside |
| XRP | 2026-06-28 | 4A | — | Failed bottom-range break; +45.0% by 8 weeks |
| XRP | 2026-08-16 | 4A | — | Re-trigger at the low; +35.0% by 4 weeks |

## Prioritized research hypotheses

These are proposals to test, not approved rule changes.

### P0 — Define an episode before changing thresholds

Separate three concepts that V0 currently conflates:

1. raw breakout/breakdown evidence,
2. a confirmed Stage 2A/4A transition,
3. continuation or re-entry evidence inside an existing trend.

Test a stateful re-arm rule based on completion of an opposite/neutral stage or
a new base/top structure. Compare it with a simple time cooldown, but do not use
the cooldown as the final definition merely because it improves this sample.

### P0 — Resolve Stage 2A versus Stage 3 inconsistency

Decide whether a Stage 2A event must have `Stage == 2`, or whether an early
breakout candidate is allowed before the Stage 2 slope threshold is met. If both
are useful, name and report them separately. Do not silently force agreement:
the three mismatched cases include both success and failure.

### P1 — Test transition timing, especially for Stage 4A

Compare the first entry into Stage 4 with later 26-week-low breakdowns. Add
sequence features such as weeks since Stage 4 began, weeks since the prior same
event, prior drawdown, and whether the support break is the first one in the
episode. This directly tests the observed capitulation problem.

### P1 — Test breakout confirmation without peeking

Evaluate a separately labeled confirmation rule, such as holding above the
broken level on the next completed week. Execution or notification must then
occur only after that confirmation week; the extra week cannot be used
retroactively.

### P2 — Improve evidence displays before the next visual pass

Add volume ratio, MA distance in ATR units, Stage, and BTC-relative-strength
panels to transition charts. The current price-only windows make it hard to
distinguish a true multi-factor transition from a price spike.

### P2 — Use episode-aware statistics

Report both raw asset-event counts and unique calendar/market episodes. Use
blocked resampling by calendar period when uncertainty estimates are added.

## Decision

Do not tune the existing numeric thresholds yet and do not expand directly to
automated alerts. The next implementation should add episode identity and the
missing diagnostic chart panels, then rerun this same frozen universe as a
semantic comparison. A broader point-in-time crypto universe should follow only
after the meaning of “new Stage 2A/4A event” is stable.
