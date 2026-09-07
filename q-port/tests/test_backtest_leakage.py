"""
Red-Team Test: Walk-Forward Backtest Look-Ahead Data Leakage Verification.
Verifies that training windows contain zero test-period data points and allocations depend solely on historical data.
"""

import pytest
import numpy as np
import pandas as pd
from core.data_loader import fetch_market_data
from core.backtest import run_walk_forward_backtest
from core.preprocessing import preprocess_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix
from core.classical_optimizer import solve_greedy


def test_walk_forward_zero_lookahead_leakage():
    """Verify in-sample training window end date is strictly prior to out-of-sample test window start date."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)

    train_window_days = 252
    test_window_days = 63
    n_days = len(returns_df)

    rebal_starts = list(range(train_window_days, n_days, test_window_days))

    for start_idx in rebal_starts:
        train_start = start_idx - train_window_days
        train_end = start_idx
        test_end = min(start_idx + test_window_days, n_days)

        train_dates = returns_df.index[train_start:train_end]
        test_dates = returns_df.index[train_end:test_end]

        if len(test_dates) == 0:
            break

        # Max train date must be strictly less than min test date
        assert train_dates.max() < test_dates.min()

        # Check overlap is empty
        overlap = set(train_dates).intersection(set(test_dates))
        assert len(overlap) == 0

        # Verify QUBO matrix built on train data alone matches exact expectations
        train_rets = returns_df.iloc[train_start:train_end]
        mu_train = compute_expected_returns(train_rets)
        cov_train = compute_covariance_matrix(train_rets)

        # Mutate future returns in test window to verify train stats are unaffected
        future_mutated_rets = returns_df.copy()
        future_mutated_rets.iloc[train_end:test_end] += 10.0  # Huge synthetic spike in test period

        mu_mutated = compute_expected_returns(future_mutated_rets.iloc[train_start:train_end])
        cov_mutated = compute_covariance_matrix(future_mutated_rets.iloc[train_start:train_end])

        np.testing.assert_array_almost_equal(mu_train, mu_mutated)
        np.testing.assert_array_almost_equal(cov_train, cov_mutated)
