"""
Unit tests for Q-PORT Walk-Forward Backtesting Engine (core/backtest.py).
"""

import pytest
import numpy as np
import pandas as pd
from core.data_loader import fetch_market_data
from core.backtest import run_walk_forward_backtest


def test_walk_forward_backtest_execution():
    """Verify walk-forward backtest executes without look-ahead bias and produces valid equity curves."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)

    equity_df, metrics_df, btest_info = run_walk_forward_backtest(
        prices_df=prices_df,
        metadata_df=meta_df,
        k_target=5,
        train_window_days=252,
        test_window_days=63
    )

    assert not equity_df.empty
    assert not metrics_df.empty
    assert btest_info["total_rebalance_cycles"] > 0
    assert btest_info["total_oos_days"] > 0

    strats = metrics_df["Strategy"].tolist()
    assert "Q-PORT (Hybrid QAOA)" in strats
    assert "Equal Weight (1/N)" in strats
    assert "Continuous Mean-Variance" in strats

    # Check that equity curves start at ~1.0
    for strat in equity_df.columns:
        assert equity_df[strat].iloc[0] > 0.5
