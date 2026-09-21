import pandas as pd

from common.universe import (
    CsvPointInTimeUniverseProvider,
    StaticUniverseProvider,
)


def test_static_universe_deduplicates_symbols():
    provider = StaticUniverseProvider("crypto-test", ("BTC/USDT", "BTC/USDT", "ETH/USDT"))

    snapshot = provider.snapshot("2026-09-21T01:00:00Z")

    assert snapshot.symbols == ("BTC/USDT", "ETH/USDT")


def test_csv_universe_uses_point_in_time_membership(tmp_path):
    path = tmp_path / "membership.csv"
    pd.DataFrame(
        {
            "symbol": ["OLD", "CURRENT", "FUTURE"],
            "effective_from": ["2020-01-01", "2024-01-01", "2027-01-01"],
            "effective_to": ["2025-01-01", None, None],
        }
    ).to_csv(path, index=False)
    provider = CsvPointInTimeUniverseProvider("sp500-history", path)

    snapshot = provider.snapshot("2026-09-21T00:00:00Z")

    assert snapshot.symbols == ("CURRENT",)
