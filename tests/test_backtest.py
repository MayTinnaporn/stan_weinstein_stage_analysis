import pandas as pd
import pytest

from common.backtest import backtest_long_transitions, summarize_trades


def make_weekly() -> pd.DataFrame:
    index = pd.date_range("2026-01-04", periods=5, freq="W-SUN", tz="UTC")
    return pd.DataFrame(
        {
            "Open": [100.0, 110.0, 120.0, 130.0, 140.0],
            "High": [105.0, 125.0, 135.0, 145.0, 150.0],
            "Low": [95.0, 108.0, 115.0, 125.0, 135.0],
            "Close": [102.0, 120.0, 130.0, 140.0, 145.0],
            "Stage2A_Event": [True, False, False, False, False],
            "Stage4A_Event": [False, False, True, False, False],
        },
        index=index,
    )


def test_backtest_executes_on_week_after_signal():
    weekly = make_weekly()
    weekly.loc[weekly.index[3], "High"] = 1_000.0
    trades = backtest_long_transitions(weekly)

    trade = trades.iloc[0]
    assert trade["EntryWeek"] == weekly.index[1]
    assert trade["EntryPrice"] == 110.0
    assert trade["ExitWeek"] == weekly.index[3]
    assert trade["ExitPrice"] == 130.0
    assert trade["GrossReturn"] == pytest.approx(130 / 110 - 1)
    assert trade["MFE"] == pytest.approx(135 / 110 - 1)


def test_backtest_applies_cost_on_each_side_and_summarizes_closed_trades():
    trades = backtest_long_transitions(
        make_weekly(),
        transaction_cost_bps_per_side=10,
    )

    expected = 130 * 0.999 / (110 * 1.001) - 1
    assert trades.iloc[0]["NetReturn"] == pytest.approx(expected)

    summary = summarize_trades(trades)
    assert summary["TradeCount"] == 1
    assert summary["WinRate"] == 1.0
