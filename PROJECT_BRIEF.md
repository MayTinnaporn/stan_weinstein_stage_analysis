# Market Stage Analysis Research Project

## 1. Objective

Build a systematic implementation of Stan Weinstein-style Stage Analysis for financial markets.

The project will contain two separately calibrated systems:

1. Cryptocurrency Stage Analysis
2. Stock Stage Analysis

The two systems share the same conceptual framework but must **not** assume that parameters, thresholds, benchmarks, volume behavior, or market structure are interchangeable.

The operational goal is a weekly research system that, every Monday morning:

1. resolves the point-in-time S&P 500 and eligible top-40 cryptocurrency universes,
2. downloads daily OHLCV and builds completed weekly bars,
3. classifies Stage 1–4 and detects new Stage 2A/4A transitions,
4. persists reproducible evidence for each run, and
5. eventually notifies the researcher of Stage 2A entry candidates and Stage 4A exit candidates.

The current goal is **not** automated trading. The project is validating whether
Weinstein-style Stage Analysis can be converted into a reproducible quantitative
market-state classifier. Notifications and an HTML infographic come only after
visual validation, forward-return analysis, and backtest refinement.

## 2. Core Concept

The market is classified into four broad stages:

- **Stage 1** — Basing / accumulation
- **Stage 2** — Advancing / uptrend
- **Stage 3** — Topping / distribution
- **Stage 4** — Declining / downtrend

Important transitions include:

- Stage 1 → Stage 2: potential **Stage 2A breakout**
- Stage 3 → Stage 4: potential **Stage 4A breakdown**

The system should use multiple pieces of evidence rather than simply `Close > 30-week moving average`.

Relevant information includes:

- Price relative to the 30-week moving average
- Direction/slope of the 30-week moving average
- Support and resistance structure
- Breakouts and breakdowns
- Volume behavior
- Relative strength
- Previous trend
- Volatility

## 3. Research Philosophy

Do not treat candidate events as validated buy/sell recommendations.

Development should proceed in this order:

1. Build features.
2. Classify market stage.
3. Visualize classifications.
4. Manually inspect whether classifications make sense.
5. Quantitatively validate forward returns by stage.
6. Tune stage-classification methodology if necessary.
7. Only afterward investigate portfolio construction or live trading strategies.

Do not assume that Weinstein Stage Analysis has predictive value. Test it empirically.

# 4. Cryptocurrency System

## 4.1 Data

Use Binance spot OHLCV through CCXT for venue-specific price and volume data.
Use CoinGecko point-in-time market-cap data to construct the weekly top-40
candidate universe. Universe selection and OHLCV acquisition are separate
responsibilities; see `docs/DATA_SOURCES.md`.

Use daily OHLCV as the raw input and aggregate daily candles into weekly candles ourselves.

Weekly definition: **Monday 00:00 UTC through Sunday 23:59 UTC.**

Avoid using incomplete weekly candles.

Initial research universe:

- BTC
- ETH
- SOL
- XRP
- BNB
- ADA
- DOGE
- LINK
- AVAX
- LTC

Begin testing with BTC, ETH, SOL and XRP before expanding the universe.

The operational universe is the top 40 eligible crypto assets by point-in-time
market capitalization. Stablecoins, wrapped/bridged duplicates, duplicate
liquid-staking exposure, ineligible venue pairs, and assets failing configured
history or liquidity requirements must be excluded by a documented policy.
Persist the input ranking, exclusions, symbol mapping, and final membership for
every run. Never backfill historical tests using today's top-40 list.

## 4.2 Crypto Features

Initial candidate features:

- Weekly OHLCV
- SMA30
- SMA30 slope over 4 weeks
- ATR14
- Price distance from SMA30 normalized by ATR
- Previous 26-week resistance
- Previous 26-week support
- 26-week range width
- Breakout flag
- Breakdown flag
- 20-week average volume
- Volume ratio
- 26-week return
- Relative strength versus BTC
- Mansfield-style relative strength versus BTC
- 4-week relative-strength slope

Resistance/support calculations must exclude the current candle where appropriate to prevent look-ahead bias.

Example:

`High.shift(1).rolling(26).max()`

rather than:

`High.rolling(26).max()`

## 4.3 Crypto Benchmark

For altcoins, use BTC as the primary relative-strength benchmark.

Distinguish:

- Stage 2 versus USD + strengthening versus BTC
- Stage 2 versus USD + weakening versus BTC

For BTC itself, do **not** calculate BTC/BTC relative strength. Initially omit relative strength for BTC.

## 4.4 Initial Crypto Classification

Start with transparent heuristic rules.

Example Stage 2 candidate:

- Close > SMA30
- SMA30 slope positive

Example Stage 4 candidate:

- Close < SMA30
- SMA30 slope negative

Stage 1 versus Stage 3 requires context from the prior trend.

Initial approximation:

- Weak/negative previous medium-term trend + flattening MA → Stage 1
- Strong/positive previous medium-term trend + flattening MA → Stage 3

These are starting hypotheses, **not final rules**. Thresholds must be configurable and empirically evaluated.

## 4.5 Crypto Stage 2A

Initial candidate evidence:

- Breakout above prior resistance
- Close above SMA30
- SMA30 not falling / preferably rising
- Increased volume
- Improving relative strength versus BTC for altcoins

A value such as `Volume Ratio >= 1.3` is an experimental parameter, not a fixed Weinstein rule.

## 4.6 Crypto Stage 4A

Candidate evidence:

- Breakdown below prior support
- Close below SMA30
- SMA30 falling
- Weakening relative strength versus BTC for altcoins

# 5. Stock System

The stock system should be implemented separately from the crypto classifier.

Shared utilities are acceptable, but classification thresholds and market assumptions should remain independent.

## 5.1 Stock Data

Use Yahoo Finance through `yfinance` for initial research data. Download daily
adjusted OHLCV and aggregate it into weekly bars. Yahoo Finance is suitable for
personal research, not assumed to be a licensed production data feed.

Weekly boundary: **trading week ending Friday**.

Corporate actions must be handled carefully. Stock splits must not appear as artificial price collapses. Dividend adjustment methodology should be explicitly documented.

The operational universe is the point-in-time S&P 500 membership on the run
date. Historical tests must use historical membership intervals rather than
today's constituents. Persist each resolved universe with the run artifacts.

## 5.2 Stock Features

Candidate features:

- Weekly OHLCV
- SMA30
- SMA30 slope
- ATR14
- Distance from SMA30
- Previous 26-week resistance
- Previous 26-week support
- Volume ratio
- Previous medium-term return
- Relative strength versus broad market
- Relative-strength slope
- Relative strength versus sector
- Sector-relative-strength slope
- Up-week volume
- Down-week volume
- Accumulation/distribution characteristics

## 5.3 Stock Benchmarks

Benchmark should be configurable by market.

Examples:

- US equities: SPY / S&P 500
- Nasdaq-focused research: QQQ
- Thailand: SET Index
- Japan: TOPIX

Do not hard-code SPY into the generic architecture.

# 6. Crypto vs Stocks

Use **one Stage Analysis concept but two independently calibrated implementations**.

Shared concepts may include:

- moving-average utilities
- ATR
- forward-return calculation
- plotting
- validation metrics
- support/resistance helpers

Asset-specific logic should remain under separate modules.

# 7. Validation

Before creating trading rules, calculate forward returns after every classified week.

Initial horizons:

- 4 weeks
- 8 weeks
- 13 weeks
- 26 weeks

For each Stage and important transition calculate:

- Observation count
- Mean forward return
- Median forward return
- Probability of positive return
- Return standard deviation
- Maximum favorable excursion
- Maximum adverse excursion

The objective is to test whether classified states correspond to statistically different future-return regimes.

# 8. Visual Validation

Before large-scale backtesting, plot:

- Close
- SMA30
- Support
- Resistance
- Stage 1/2/3/4
- Stage 2A
- Stage 4A

First manually inspect BTC, ETH, SOL and XRP.

# 9. Bias and Research Risks

Guard explicitly against:

- Look-ahead bias
- Incomplete candles
- Survivorship bias
- Selection bias
- Parameter overfitting
- Data leakage

For stocks also consider delisted companies, historical index membership and corporate actions.

For crypto consider delisted tokens, exchange-specific history, volume fragmentation, thin liquidity, wash trading and short asset histories.

# 10. Out of Scope During Research Validation

Do **not** implement yet:

- Anomaly-detection framework
- Machine-learning Stage classifier
- HMM Stage classifier
- Automated trading
- Position sizing
- Portfolio optimization
- Live execution
- Exchange API trading
- Production notification delivery
- Production HTML infographic

Previous anomaly-detection discussions were conceptual only; no anomaly system has been implemented.

A small event-driven backtester is in scope as a research instrument. It may
simulate entry on a new Stage 2A event and exit on a new Stage 4A event at the
following weekly open, with explicit costs. This does not make the classifier a
validated strategy and must not evolve into live execution during this phase.

# 11. Development Status and Immediate Milestone

## Completed foundation

- Separate cryptocurrency and stock V0 classifiers
- Daily-to-weekly aggregation with incomplete-week exclusion
- Feature calculation, Stage 1–4 labels, and Stage 2A/4A candidate flags
- Rising-edge Stage 2A/4A event detection
- Charts and forward-return summaries
- Reproducible as-of batch runs with persisted inputs, outputs, and configuration hash
- Point-in-time CSV universe support
- Research-only transition backtester
- Frozen-rule crypto walk-forward validation reports
- UV-managed Python environment and lockfile

## Immediate implementation milestone

1. Finish visual and quantitative validation on BTC, ETH, SOL, and XRP.
2. Implement and test the CoinGecko point-in-time top-40 universe provider,
   eligibility rules, and CoinGecko-to-Binance symbol mapping.
3. Acquire and validate a reliable point-in-time S&P 500 membership dataset.
4. Run transition-level forward-return and walk-forward backtests without tuning
   on future data.
5. Define notification state/idempotency and delivery only after the candidate
   semantics are accepted.
6. Build the HTML infographic after the stored result schema stabilizes.

Do not optimize parameters yet.

# 12. Coding Principles

Prefer:

- Python
- Functional, modular code
- Type hints
- Clear docstrings
- Configuration rather than hard-coded thresholds
- pandas initially
- Unit tests for feature calculations
- Explicit protection against look-ahead bias

Functions should have a single clear responsibility. Research assumptions should be documented rather than silently embedded in code.

# 13. Tooling and Data-Source Decisions

- Use UV for Python version, virtual environment, dependency, and lockfile management.
- Use Yahoo Finance through `yfinance` for stock research OHLCV during the initial research phase.
- Use Binance spot OHLCV through CCXT for crypto price and venue-specific volume data.
- Use CoinGecko point-in-time market-cap data to define the weekly top-40 cryptocurrency universe.
- Persist each weekly universe snapshot; do not reconstruct historical membership from today's rankings.
- Keep universe selection separate from tradable OHLCV acquisition.
