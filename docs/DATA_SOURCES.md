# Data Source Policy

## Stocks

Research OHLCV is acquired from Yahoo Finance through `yfinance` with adjusted
OHLC enabled by default. Adjustment behavior, weekly aggregation, and benchmark
alignment must remain covered by tests.

Yahoo Finance is appropriate for this personal research phase. The `yfinance`
project states that it is an unofficial research/educational client and that
Yahoo data is intended for personal use. A licensed market-data provider should
be evaluated before commercial distribution or production-grade alerting.

Historical S&P 500 backtests must use point-in-time constituent membership.
Today's index members must never be projected backward through the test period.

## Cryptocurrencies

Use separate sources for two different questions.

### Universe membership: CoinGecko

CoinGecko is the recommended source for market capitalization and the weekly
top-40 universe snapshot. The operational Monday run should persist the exact
CoinGecko IDs, ranks, market caps, exclusions, and retrieval timestamp used in
that run.

The top-40 policy should exclude at least:

- stablecoins,
- wrapped or bridged duplicates,
- liquid-staking representations when they duplicate the underlying exposure,
- assets without an eligible spot pair on the configured execution venue,
- assets failing the configured history or liquidity minimum.

For historical backtests, use point-in-time market caps. CoinGecko's historical
coin endpoint returns a 00:00 UTC snapshot containing price, market cap, and
volume for a requested date. Full history requires an appropriate paid plan;
the Basic plan is limited to recent history. Reconstructing historical ranks
also requires an unbiased candidate set, not only today's surviving coins.

### Tradable OHLCV: Binance through CCXT

Continue using Binance spot daily OHLCV through CCXT for the initial system.
This provides actual venue-specific open, high, low, close, and volume data for
the intended tradable pair rather than an aggregated reference price.

The source exchange and pair must be stored with every snapshot. If a top-40
asset lacks the configured Binance spot pair, mark it ineligible or apply a
documented fallback exchange policy; never silently substitute a different
market during a backtest.

Exchange gaps, listing dates, delistings, quote-currency changes, and missing
candles are data-quality events. The pipeline should fail closed for affected
weeks and record the reason.

## Recommended Architecture

```text
CoinGecko point-in-time market caps
            ↓
top-40 eligibility and exclusions
            ↓
CoinGecko ID ↔ venue symbol mapping
            ↓
Binance/CCXT daily OHLCV
            ↓
completed weekly bars and Stage Analysis
```

This separation prevents market-cap rankings from being inferred from one
exchange's listing universe while keeping price and volume tied to a market
that could actually be traded.
