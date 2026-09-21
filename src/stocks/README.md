# Stock Stage Analysis V0

This folder contains a complete first-pass stock implementation.

Key stock-specific differences from crypto:

- daily data is downloaded with yfinance,
- data is adjusted for splits/dividends by default,
- weekly bars end Friday,
- market-relative Mansfield RS is supported,
- optional sector-relative Mansfield RS is supported,
- stock thresholds remain independent from crypto thresholds.

This implementation is intentionally transparent and simple so it can be visually validated before refinement.
