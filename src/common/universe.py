from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from common.time import to_utc_timestamp


@dataclass(frozen=True)
class UniverseSnapshot:
    """Point-in-time asset membership used by one research run."""

    name: str
    as_of: pd.Timestamp
    symbols: tuple[str, ...]

    def __post_init__(self) -> None:
        cleaned = tuple(dict.fromkeys(symbol.strip() for symbol in self.symbols if symbol.strip()))
        if not cleaned:
            raise ValueError("Universe snapshot must contain at least one symbol")
        object.__setattr__(self, "symbols", cleaned)
        object.__setattr__(self, "as_of", to_utc_timestamp(self.as_of))


class UniverseProvider(Protocol):
    """Interface for static or point-in-time universe membership sources."""

    def snapshot(self, as_of: str | pd.Timestamp) -> UniverseSnapshot:
        """Return membership known at ``as_of``."""


@dataclass(frozen=True)
class StaticUniverseProvider:
    """Fixed universe suitable for initial visual validation only."""

    name: str
    symbols: tuple[str, ...]

    def snapshot(self, as_of: str | pd.Timestamp) -> UniverseSnapshot:
        return UniverseSnapshot(self.name, to_utc_timestamp(as_of), self.symbols)


@dataclass(frozen=True)
class CsvPointInTimeUniverseProvider:
    """Load dated membership from a CSV file.

    Required columns are ``symbol`` and ``effective_from``. ``effective_to``
    is optional and exclusive; a blank value means the membership is active.
    """

    name: str
    path: str | Path

    def snapshot(self, as_of: str | pd.Timestamp) -> UniverseSnapshot:
        as_of_ts = to_utc_timestamp(as_of)
        membership = pd.read_csv(self.path)
        required = {"symbol", "effective_from"}
        missing = required.difference(membership.columns)
        if missing:
            raise ValueError(f"Universe CSV is missing columns: {sorted(missing)}")

        effective_from = pd.to_datetime(membership["effective_from"], utc=True)
        if "effective_to" in membership.columns:
            effective_to = pd.to_datetime(
                membership["effective_to"],
                utc=True,
                errors="coerce",
            )
        else:
            effective_to = pd.Series(pd.NaT, index=membership.index, dtype="datetime64[ns, UTC]")

        active = (effective_from <= as_of_ts) & (
            effective_to.isna() | (as_of_ts < effective_to)
        )
        symbols = tuple(membership.loc[active, "symbol"].astype(str))
        return UniverseSnapshot(self.name, as_of_ts, symbols)
