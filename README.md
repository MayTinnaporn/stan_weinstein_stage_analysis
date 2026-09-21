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

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

## Run Crypto

```bash
python main.py crypto --symbol BTC/USDT
python main.py crypto --symbol ETH/USDT
python main.py crypto --symbol SOL/USDT
python main.py crypto --symbol XRP/USDT
```

## Run Stocks

```bash
python main.py stock --symbol AAPL
python main.py stock --symbol NVDA --sector SMH
python main.py stock --symbol MSFT --sector XLK
```

Outputs are written under `outputs/`.

## Tests

```bash
pytest -q
```

## Codex

Open the repository in Codex Desktop and ask it to read:

- `AGENTS.md`
- `PROJECT_BRIEF.md`
- `CODEX_START_PROMPT.md`

The repository already contains both V0 implementations. Codex should **review and refine**, not redesign from scratch.

The first validation priority remains the crypto system, but the stock code is present and ready for later review.
