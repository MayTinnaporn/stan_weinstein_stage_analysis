from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from common.models import AnalysisBundle
from common.time import to_utc_timestamp
from common.transitions import add_transition_events
from crypto.classifier import classify_crypto_stage, detect_stage2a, detect_stage4a
from crypto.data_loader import fetch_daily_ohlcv
from crypto.features import add_stage_features
from crypto.preprocessing import daily_to_weekly

logger = logging.getLogger(__name__)


def build_crypto_analysis(
    target_daily: pd.DataFrame,
    config: dict[str, Any],
    *,
    benchmark_daily: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build crypto features and labels from already acquired daily data."""
    week_rule = config["data"]["week_rule"]
    features_cfg = config["features"]
    classifier_cfg = config["classifier"]

    target_weekly = daily_to_weekly(
        target_daily,
        week_rule=week_rule,
    )
    benchmark_weekly = (
        daily_to_weekly(benchmark_daily, week_rule=week_rule)
        if benchmark_daily is not None
        else None
    )

    result = add_stage_features(
        target_weekly,
        btc_weekly=benchmark_weekly,
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
    result = add_transition_events(result)

    return result


def analyze_crypto_bundle(
    symbol: str,
    config: dict[str, Any],
    *,
    as_of: str | pd.Timestamp | None = None,
    target_daily: pd.DataFrame | None = None,
    benchmark_daily: pd.DataFrame | None = None,
) -> AnalysisBundle:
    """Acquire and analyze one crypto symbol as of a reproducible timestamp."""
    as_of_ts = to_utc_timestamp(as_of)
    exchange_id = config["exchange"]["id"]
    start = config["data"]["start"]
    benchmark_symbol = config["research"]["benchmark_symbol"]
    end = (as_of_ts.normalize() - pd.Timedelta(days=1)).date().isoformat()

    if target_daily is None:
        target_daily = fetch_daily_ohlcv(
            symbol=symbol,
            start=start,
            end=end,
            exchange_id=exchange_id,
        )

    benchmark_for_features = None
    if symbol != benchmark_symbol:
        if benchmark_daily is None:
            benchmark_daily = fetch_daily_ohlcv(
                symbol=benchmark_symbol,
                start=start,
                end=end,
                exchange_id=exchange_id,
            )
        benchmark_for_features = benchmark_daily

    weekly = daily_to_weekly(target_daily, week_rule=config["data"]["week_rule"])
    result = build_crypto_analysis(
        target_daily,
        config,
        benchmark_daily=benchmark_for_features,
    )

    logger.info(
        "Completed Stage Analysis for %s with %d weekly rows as of %s",
        symbol,
        len(result),
        as_of_ts.isoformat(),
    )
    return AnalysisBundle("crypto", symbol, as_of_ts, target_daily, weekly, result)


def analyze_crypto(
    symbol: str,
    config: dict[str, Any],
    *,
    as_of: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Run the Stage Analysis pipeline for one crypto symbol."""
    return analyze_crypto_bundle(symbol, config, as_of=as_of).analysis
