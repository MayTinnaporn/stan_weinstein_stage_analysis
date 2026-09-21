import numpy as np
import pandas as pd

from stocks.features import add_stage_features, calculate_mansfield_rs


def make_weekly(periods: int = 90, scale: float = 1.0) -> pd.DataFrame:
    idx = pd.date_range(
        "2024-01-05",
        periods=periods,
        freq="W-FRI",
        tz="UTC",
    )

    close = pd.Series(
        np.linspace(100, 200, periods) * scale,
        index=idx,
    )

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


def test_mansfield_relative_strength_columns():
    asset = make_weekly()
    benchmark = make_weekly(scale=0.7)

    rs = calculate_mansfield_rs(
        asset["Close"],
        benchmark["Close"],
        prefix="Market",
    )

    assert "RS_Market" in rs.columns
    assert "Mansfield_RS_Market" in rs.columns
    assert "RS_Market_slope_4w" in rs.columns


def test_stock_resistance_excludes_current_week():
    weekly = make_weekly(50)
    weekly.iloc[-1, weekly.columns.get_loc("High")] = 9999.0

    out = add_stage_features(
        weekly,
        structure_lookback=26,
    )

    assert out["Resistance_26w"].iloc[-1] < 9999.0


def test_market_and_sector_rs_are_added():
    asset = make_weekly()
    market = make_weekly(scale=0.8)
    sector = make_weekly(scale=0.9)

    out = add_stage_features(
        asset,
        market_weekly=market,
        sector_weekly=sector,
    )

    assert "Mansfield_RS_Market" in out.columns
    assert "Mansfield_RS_Sector" in out.columns
