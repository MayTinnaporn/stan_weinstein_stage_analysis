from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from stocks.classifier import classify_stock_stage, detect_stage2a, detect_stage4a
from stocks.data_loader import fetch_daily_ohlcv
from stocks.features import add_stage_features
from stocks.preprocessing import daily_to_weekly

logger = logging.getLogger(__name__)


def analyze_stock(
    symbol: str,
    config: dict[str, Any],
    *,
    sector_symbol: str | None = None,
) -> pd.DataFrame:
    """Run the V0 Stage Analysis pipeline for one stock."""
    start = config["data"]["start"]
    auto_adjust = bool(config["data"]["auto_adjust"])
    week_rule = config["data"]["week_rule"]

    market_symbol = config["research"]["market_benchmark"]
    if sector_symbol is None:
        sector_symbol = config["research"].get("default_sector_benchmark")

    features_cfg = config["features"]
    classifier_cfg = config["classifier"]

    market_daily = fetch_daily_ohlcv(
        symbol=market_symbol,
        start=start,
        auto_adjust=auto_adjust,
    )
    market_weekly = daily_to_weekly(
        market_daily,
        week_rule=week_rule,
    )

    target_daily = fetch_daily_ohlcv(
        symbol=symbol,
        start=start,
        auto_adjust=auto_adjust,
    )
    target_weekly = daily_to_weekly(
        target_daily,
        week_rule=week_rule,
    )

    sector_weekly = None
    if sector_symbol:
        sector_daily = fetch_daily_ohlcv(
            symbol=sector_symbol,
            start=start,
            auto_adjust=auto_adjust,
        )
        sector_weekly = daily_to_weekly(
            sector_daily,
            week_rule=week_rule,
        )

    result = add_stage_features(
        target_weekly,
        market_weekly=market_weekly,
        sector_weekly=sector_weekly,
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

    logger.info(
        "Completed Stock Stage Analysis for %s with %d weekly rows",
        symbol,
        len(result),
    )

    return result
