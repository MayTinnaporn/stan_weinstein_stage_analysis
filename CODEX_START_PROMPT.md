# Initial Codex Handoff Prompt

Please read `AGENTS.md` and `PROJECT_BRIEF.md` first.

This repository already contains **both V0 implementations**:

- Cryptocurrency Stage Analysis
- Stock Stage Analysis

Do **not** redesign the project from scratch.

## First priority: Crypto review

Review:
- `src/crypto/data_loader.py`
- `src/crypto/preprocessing.py`
- `src/crypto/features.py`
- `src/crypto/classifier.py`
- `src/crypto/pipeline.py`
- `src/crypto/validation.py`
- `src/crypto/visualization.py`

Check:
1. correctness,
2. look-ahead bias/data leakage,
3. Monday-Sunday UTC aggregation,
4. incomplete-week handling,
5. SMA30, ATR14, support/resistance, volume ratio and BTC-relative strength,
6. Stage 1/2/3/4 logic,
7. Stage 2A/4A logic,
8. configuration separation,
9. tests.

Initial crypto universe:
- BTC/USDT
- ETH/USDT
- SOL/USDT
- XRP/USDT

## Stock V0 is already present

Do not delete or redesign it. The stock implementation includes:
- yfinance adjusted OHLCV,
- Friday-ending weekly aggregation,
- 30-week SMA,
- ATR14,
- 26-week support/resistance,
- volume ratio,
- Mansfield RS vs market benchmark,
- Mansfield RS vs optional sector benchmark,
- Stage 1/2/3/4,
- Stage 2A/4A,
- plotting and forward-return validation.

Stock files live under `src/stocks/`.

The stock implementation should be reviewed only after the crypto V0 has been visually validated, unless explicitly instructed otherwise.

Do **not** yet:
- optimize thresholds,
- implement trading entry/exit rules,
- add anomaly detection,
- implement ML/HMM,
- build live trading.

The purpose of the first iteration is visual validation, not parameter optimization.
