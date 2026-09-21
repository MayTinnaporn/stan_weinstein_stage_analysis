from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from common.models import AnalysisBundle
from common.time import to_utc_timestamp
from common.transitions import add_transition_events
from stocks.classifier import classify_stock_stage, detect_stage2a, detect_stage4a
from stocks.data_loader import fetch_daily_ohlcv
from stocks.features import add_stage_features
from stocks.preprocessing import daily_to_weekly

logger = logging.getLogger(__name__)


def build_stock_analysis(
    target_daily: pd.DataFrame,
    config: dict[str, Any],
    *,
    as_of: str | pd.Timestamp,
    symbol: str,
    market_daily: pd.DataFrame | None = None,
    market_symbol: str | None = None,
    sector_daily: pd.DataFrame | None = None,
    sector_symbol: str | None = None,
) -> pd.DataFrame:
    """Build stock features and labels from already acquired daily data."""
    week_rule = config["data"]["week_rule"]
    features_cfg = config["features"]
    classifier_cfg = config["classifier"]

    target_weekly = daily_to_weekly(
        target_daily,
        week_rule=week_rule,
        as_of=as_of,
    )
    market_weekly = (
        daily_to_weekly(market_daily, week_rule=week_rule, as_of=as_of)
        if market_daily is not None
        else None
    )
    sector_weekly = (
        daily_to_weekly(sector_daily, week_rule=week_rule, as_of=as_of)
        if sector_daily is not None
        else None
    )

    market_for_features = (
        None if symbol == market_symbol else market_weekly
    )
    sector_for_features = (
        None if symbol == sector_symbol else sector_weekly
    )

    result = add_stage_features(
        target_weekly,
        market_weekly=market_for_features,
        sector_weekly=sector_for_features,
        ma_period=int(features_cfg["ma_period"]),
        ma_slope_period=int(features_cfg["ma_slope_period"]),
        atr_period=int(features_cfg["atr_period"]),
        structure_lookback=int(features_cfg["structure_lookback"]),
        volume_lookback=int(features_cfg["volume_lookback"]),
        momentum_lookback=int(features_cfg["momentum_lookback"]),
        rs_lookback=int(features_cfg["rs_lookback"]),
        rs_slope_period=int(features_cfg["rs_slope_period"]),
    )

    result = classify_stock_stage(
        result,
        slope_threshold=float(classifier_cfg["ma_slope_threshold"]),
    )
    result = detect_stage2a(
        result,
        min_volume_ratio=float(classifier_cfg["stage2a_min_volume_ratio"]),
    )
    result = detect_stage4a(result)
    return add_transition_events(result)


def analyze_stock_bundle(
    symbol: str,
    config: dict[str, Any],
    *,
    sector_symbol: str | None = None,
    as_of: str | pd.Timestamp | None = None,
    target_daily: pd.DataFrame | None = None,
    market_daily: pd.DataFrame | None = None,
    sector_daily: pd.DataFrame | None = None,
) -> AnalysisBundle:
    """Acquire and analyze one stock as of a reproducible timestamp."""
    as_of_ts = to_utc_timestamp(as_of)
    start = config["data"]["start"]
    auto_adjust = bool(config["data"]["auto_adjust"])
    week_rule = config["data"]["week_rule"]
    market_symbol = config["research"]["market_benchmark"]
    if sector_symbol is None:
        sector_symbol = config["research"].get("default_sector_benchmark")
    end = as_of_ts.date().isoformat()

    if target_daily is None:
        target_daily = fetch_daily_ohlcv(
            symbol=symbol,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
        )

    if symbol != market_symbol and market_daily is None:
        market_daily = fetch_daily_ohlcv(
            symbol=market_symbol,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
        )

    if sector_symbol and symbol != sector_symbol and sector_daily is None:
        sector_daily = fetch_daily_ohlcv(
            symbol=sector_symbol,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
        )

    weekly = daily_to_weekly(
        target_daily,
        week_rule=week_rule,
        as_of=as_of_ts,
    )
    result = build_stock_analysis(
        target_daily,
        config,
        as_of=as_of_ts,
        symbol=symbol,
        market_daily=market_daily,
        market_symbol=market_symbol,
        sector_daily=sector_daily,
        sector_symbol=sector_symbol,
    )

    logger.info(
        "Completed Stock Stage Analysis for %s with %d weekly rows as of %s",
        symbol,
        len(result),
        as_of_ts.isoformat(),
    )
    return AnalysisBundle("stocks", symbol, as_of_ts, target_daily, weekly, result)


def analyze_stock(
    symbol: str,
    config: dict[str, Any],
    *,
    sector_symbol: str | None = None,
    as_of: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Run the Stage Analysis pipeline for one stock."""
    return analyze_stock_bundle(
        symbol,
        config,
        sector_symbol=sector_symbol,
        as_of=as_of,
    ).analysis
