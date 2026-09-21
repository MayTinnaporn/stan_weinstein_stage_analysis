# Market Stage Analysis

Research implementation of Stan Weinstein-style Stage Analysis with **separate V0 engines for cryptocurrencies and stocks**.

The two systems share the same conceptual framework but are intentionally calibrated independently.

## Repository Scope

### Crypto V0
- CCXT daily OHLCV
- Monday-Sunday UTC weekly bars
- 30-week SMA and slope
- ATR(14)
- 26-week support/resistance
- volume ratio
- 26-week momentum
- Mansfield-style relative strength vs BTC for altcoins
- Stage 1/2/3/4
- Stage 2A / Stage 4A candidates
- plotting and forward-return validation

### Stock V0
- yfinance daily adjusted OHLCV
- trading week ending Friday
- 30-week SMA and slope
- ATR(14)
- 26-week support/resistance
- volume ratio
- 26-week momentum
- Mansfield-style relative strength vs market benchmark
- Mansfield-style relative strength vs optional sector benchmark
- Stage 1/2/3/4
- Stage 2A / Stage 4A candidates
- plotting and forward-return validation

Both classifiers are **research hypotheses**, not trading strategies.

## Current Status

Implemented now:

- both V0 classifiers and visualizations,
- reproducible single-asset and batch runs,
- static and CSV point-in-time universe inputs,
- forward-return summaries and a research-only transition backtester.

Still to implement:

- live CoinGecko top-40 universe resolution and symbol eligibility mapping,
- an authoritative historical S&P 500 membership feed,
- Monday scheduling and idempotent notifications,
- the HTML infographic.

See `PROJECT_BRIEF.md` for research assumptions and `docs/OPERATIONS.md` for the
target weekly workflow and implementation boundary.

## Setup

```bash
uv sync
```

UV manages the Python version, virtual environment, dependencies, and the
committed `uv.lock`. Add or remove packages with `uv add` and `uv remove`.

## Run Crypto

```bash
uv run python main.py crypto --symbol BTC/USDT
uv run python main.py crypto --symbol ETH/USDT
uv run python main.py crypto --symbol SOL/USDT
uv run python main.py crypto --symbol XRP/USDT
```

## Run Stocks

```bash
uv run python main.py stock --symbol AAPL
uv run python main.py stock --symbol NVDA --sector SMH
uv run python main.py stock --symbol MSFT --sector XLK
```

Outputs are written under `outputs/`.

## Reproducible Batch Runs

Every research run can be pinned to an explicit UTC timestamp. Batch runs
persist raw daily data, completed weekly bars, analysis, transition events,
the universe snapshot and configuration hash under a timestamped directory.

```bash
uv run python main.py crypto-batch \
  --as-of 2026-09-21T01:00:00Z \
  --symbols BTC/USDT ETH/USDT SOL/USDT XRP/USDT

uv run python main.py stock-batch \
  --as-of 2026-09-21T01:00:00Z \
  --symbols AAPL MSFT NVDA AMZN
```

For backtests, provide a point-in-time membership CSV rather than today's
constituents:

```csv
symbol,effective_from,effective_to
AAPL,1982-11-30,
OLD_MEMBER,2010-01-01,2018-06-01
```

```bash
uv run python main.py stock-batch \
  --as-of 2017-01-09T01:00:00Z \
  --universe-name sp500-history \
  --universe-csv data/sp500_membership.csv
```

Static symbol lists are intended for initial visual validation only. Historical
testing of today's S&P 500 or today's top-40 cryptocurrencies would introduce
survivorship or selection bias.

The intended production cadence is Monday after the crypto week has closed and
source data is available. The recommended default is `01:00 UTC` (`08:00
Asia/Bangkok`). Scheduling itself is not yet included in the repository.

## Transition Backtest

Stage 2A/4A candidates are converted into rising-edge event columns so a
multiweek candidate produces only one event. The initial long-only backtester
executes each event at the following weekly open and supports per-side costs.

```bash
uv run python main.py backtest \
  --input outputs/runs/20260921T010000Z/crypto/ETH_USDT/analysis.csv \
  --cost-bps-per-side 10
```

This remains a research tool, not a live trading or position-sizing system.

## Crypto Walk-Forward Validation

Validate a persisted crypto batch without changing classifier thresholds:

```bash
uv run python main.py crypto-validate \
  --run-dir outputs/runs/20260921T010000Z \
  --min-history-weeks 104 \
  --test-window-weeks 52 \
  --cost-bps-per-side 0 10 25
```

The command verifies that `config/crypto.yaml` matches the batch configuration
hash, then writes:

- event-level 4/8/13/26-week return, MFE, MAE, and censoring data,
- per-fold and all-fold summaries,
- Stage 2A-entry/Stage 4A-exit cost sensitivity,
- fold definitions, source hashes, and the frozen configuration,
- focused charts around every transition,
- a Markdown baseline report.

By default, results are saved under the batch's
`crypto/walk_forward_validation/` directory. The folds are chronological
evaluation blocks; the rules are not fitted or tuned inside them.

## Tests

```bash
uv run pytest -q
```

## Data Sources

- Stocks: Yahoo Finance through `yfinance`, with adjusted OHLC enabled by
  default to protect the research from artificial split gaps.
- Crypto OHLCV: Binance spot markets through CCXT. These candles and volumes
  are exchange-specific, which keeps the backtest tied to a tradable venue.
- Crypto universe: CoinGecko is the recommended source for point-in-time
  market capitalization and the weekly top-40 membership snapshot.

See:

- `docs/DATA_SOURCES.md` for universe/OHLCV separation, historical-data
  limitations, and fallback policy.
- `docs/OPERATIONS.md` for the Monday workflow, artifacts, failure handling,
  and notification boundary.
- `docs/VALIDATION_LOG.md` for recorded visual and mechanical checks.

## Codex

Open the repository in Codex Desktop and ask it to read:

- `AGENTS.md`
- `PROJECT_BRIEF.md`
- `CODEX_START_PROMPT.md`

The repository already contains both V0 implementations. Codex should **review and refine**, not redesign from scratch.

The first validation priority remains the crypto system, but the stock code is present and ready for later review.
