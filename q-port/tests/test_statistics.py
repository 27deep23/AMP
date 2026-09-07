"""
Unit tests for Q-PORT statistics engine and data processing.
Validates financial metric calculations against hand-calculated analytical baselines.
"""

import pytest
import numpy as np
import pandas as pd
from core.data_loader import fetch_market_data, load_bundled_asset_metadata, load_bundled_prices
from core.preprocessing import preprocess_data
from core.statistics import (
    compute_expected_returns,
    compute_covariance_matrix,
    compute_portfolio_stats,
    compute_max_drawdown,
    compute_asset_statistics
)


def test_data_loader_bundled():
    """Verify bundled data loader returns valid dataset without NaNs."""
    prices_df, meta_df, report = fetch_market_data(force_bundled=True)
    assert not prices_df.empty
    assert len(prices_df.columns) >= 15
    assert prices_df.isna().sum().sum() == 0
    assert report["source"] == "Bundled Reproducible Dataset (Judge Mode)"
    assert len(meta_df) == len(prices_df.columns)


def test_preprocessing():
    """Verify daily returns calculation and metadata alignment."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    clean_prices, returns_df, clean_meta, prep_stats = preprocess_data(prices_df, meta_df)
    
    assert len(returns_df) == len(clean_prices) - 1
    assert list(returns_df.columns) == list(clean_prices.columns)
    assert list(clean_meta["Ticker"]) == list(clean_prices.columns)
    assert prep_stats["final_asset_count"] == len(clean_prices.columns)


def test_covariance_properties():
    """Verify symmetry and positive definiteness of regularized covariance matrix."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    _, returns_df, _, _ = preprocess_data(prices_df, meta_df)
    
    cov = compute_covariance_matrix(returns_df, epsilon=1e-6)
    
    # 1. Symmetry
    assert np.allclose(cov, cov.T)
    
    # 2. Positive definiteness (all eigenvalues > 0)
    eigenvalues = np.linalg.eigvalsh(cov)
    assert np.all(eigenvalues > 0)


def test_portfolio_stats_hand_calculated():
    """
    Spot-check portfolio metrics against hand-calculated analytical baselines.
    Setup:
      mu = [0.10, 0.20]
      Sigma = [[0.04, 0.01], [0.01, 0.09]]
      w = [0.5, 0.5]
      Rf = 0.05
      
    Expected:
      mu_p = 0.5*0.10 + 0.5*0.20 = 0.15
      sigma2_p = 0.25*0.04 + 2*(0.25)*0.01 + 0.25*0.09 = 0.0375
      sigma_p = sqrt(0.0375) = 0.1936491673
      Sharpe = (0.15 - 0.05) / 0.1936491673 = 0.5163977795
      HHI = 0.5^2 + 0.5^2 = 0.50
    """
    mu = np.array([0.10, 0.20])
    cov = np.array([[0.04, 0.01], [0.01, 0.09]])
    w = np.array([0.5, 0.5])
    rf = 0.05

    meta = pd.DataFrame({"Ticker": ["A", "B"], "Name": ["Asset A", "Asset B"], "Sector": ["Tech", "Fin"]})

    stats = compute_portfolio_stats(w, mu, cov, metadata_df=meta, risk_free_rate=rf)

    assert pytest.approx(stats["expected_return"], abs=1e-6) == 0.15
    assert pytest.approx(stats["variance"], abs=1e-6) == 0.0375
    assert pytest.approx(stats["volatility"], abs=1e-6) == np.sqrt(0.0375)
    assert pytest.approx(stats["sharpe_ratio"], abs=1e-6) == (0.15 - 0.05) / np.sqrt(0.0375)
    assert pytest.approx(stats["hhi"], abs=1e-6) == 0.50
    assert stats["active_asset_count"] == 2
    assert stats["sector_exposures"]["Tech"] == 0.5
    assert stats["sector_exposures"]["Fin"] == 0.5


def test_max_drawdown():
    """Verify max drawdown on a known daily return series."""
    # Prices: 100 -> 150 -> 120 -> 90 -> 135
    # Daily returns: +0.50, -0.20, -0.25, +0.50
    daily_rets = np.array([0.50, -0.20, -0.25, 0.50])
    max_dd, cum_series, cagr = compute_max_drawdown(daily_rets)
    
    # Peak = 1.50, Trough = 0.90 => Drawdown = (1.50 - 0.90) / 1.50 = 0.40 (40%)
    assert pytest.approx(max_dd, abs=1e-6) == 0.40
    assert pytest.approx(cum_series[-1], abs=1e-6) == 1.35
