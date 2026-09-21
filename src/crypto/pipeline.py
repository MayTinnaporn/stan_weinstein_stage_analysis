from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from crypto.classifier import classify_crypto_stage, detect_stage2a, detect_stage4a
from crypto.data_loader import fetch_daily_ohlcv
from crypto.features import add_stage_features
from crypto.preprocessing import daily_to_weekly

logger = logging.getLogger(__name__)


def analyze_crypto(
    symbol: str,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Run the V0 Stage Analysis pipeline for one crypto symbol."""
    exchange_id = config["exchange"]["id"]
    start = config["data"]["start"]
    week_rule = config["data"]["week_rule"]

    benchmark_symbol = config["research"]["benchmark_symbol"]
    features_cfg = config["features"]
    classifier_cfg = config["classifier"]

    benchmark_daily = fetch_daily_ohlcv(
        symbol=benchmark_symbol,
        start=start,
        exchange_id=exchange_id,
    )
    benchmark_weekly = daily_to_weekly(
        benchmark_daily,
        week_rule=week_rule,
    )

    target_daily = fetch_daily_ohlcv(
        symbol=symbol,
        start=start,
        exchange_id=exchange_id,
    )
    target_weekly = daily_to_weekly(
        target_daily,
        week_rule=week_rule,
    )

    btc_weekly = None if symbol == benchmark_symbol else benchmark_weekly

    result = add_stage_features(
        target_weekly,
        btc_weekly=btc_weekly,
        ma_period=int(features_cfg["ma_period"]),
        ma_slope_period=int(features_cfg["ma_slope_period"]),
        atr_period=int(features_cfg["atr_period"]),
        structure_lookback=int(features_cfg["structure_lookback"]),
        volume_lookback=int(features_cfg["volume_lookback"]),
        momentum_lookback=int(features_cfg["momentum_lookback"]),
        rs_lookback=int(features_cfg["rs_lookback"]),
        rs_slope_period=int(features_cfg["rs_slope_period"]),
    )

    result = classify_crypto_stage(
        result,
        slope_threshold=float(classifier_cfg["ma_slope_threshold"]),
    )

    result = detect_stage2a(
        result,
        min_volume_ratio=float(classifier_cfg["stage2a_min_volume_ratio"]),
    )

    result = detect_stage4a(result)

    logger.info(
        "Completed Stage Analysis for %s with %d weekly rows",
        symbol,
        len(result),
    )

    return result
