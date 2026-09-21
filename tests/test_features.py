import numpy as np
import pandas as pd

from crypto.features import add_stage_features, calculate_atr


def make_weekly(periods: int = 80) -> pd.DataFrame:
    idx = pd.date_range(
        "2024-01-07",
        periods=periods,
        freq="W-SUN",
        tz="UTC",
    )

    close = pd.Series(np.linspace(100, 200, periods), index=idx)

    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 2.0,
            "Low": close - 2.0,
            "Close": close,
            "Volume": 1000.0,
        },
        index=idx,
    )


def test_atr_positive_after_warmup():
    weekly = make_weekly()
    atr = calculate_atr(weekly, period=14)

    assert atr.iloc[:13].isna().all()
    assert (atr.iloc[13:] > 0).all()


def test_resistance_excludes_current_week():
    weekly = make_weekly(40)
    weekly.iloc[-1, weekly.columns.get_loc("High")] = 9999.0

    out = add_stage_features(weekly, structure_lookback=26)

    assert out["Resistance_26w"].iloc[-1] < 9999.0


def test_altcoin_relative_strength_columns_exist():
    weekly = make_weekly()
    btc = make_weekly()
    btc["Close"] = btc["Close"] * 2.0

    out = add_stage_features(weekly, btc_weekly=btc)

    assert "RS_BTC" in out.columns
    assert "Mansfield_RS_BTC" in out.columns
    assert "RS_BTC_slope_4w" in out.columns
