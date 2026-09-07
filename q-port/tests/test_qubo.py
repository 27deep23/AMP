"""
Unit tests for QUBO construction, sector target allocation, and penalty calibration.
"""

import pytest
import numpy as np
import pandas as pd
from core.qubo import allocate_sector_targets, calibrate_penalties, build_qubo_matrix


def test_allocate_sector_targets():
    """Verify sector targets allocation using largest-remainder method sums to K."""
    sectors = ["Tech", "Tech", "Tech", "Fin", "Fin", "Energy", "Energy", "Cons", "Cons", "Cons"]
    k_target = 5
    targets = allocate_sector_targets(sectors, k_target)

    assert sum(targets.values()) == k_target
    assert targets["Tech"] >= 1
    assert targets["Cons"] >= 1


def test_calibrate_penalties():
    """Verify penalty calibration scales with return/risk swing."""
    mu = np.array([0.10, 0.30])
    cov = np.array([[0.04, 0.0], [0.0, 0.09]])
    
    # swing_bound = max_abs_ret * N + risk_aversion * max_eig * N^2 = 0.30 * 2 + 1.0 * 0.09 * 4 = 0.60 + 0.36 = 0.96
    # multiplier = 2.0 => penalty = 1.92
    penalty_A, swing_bound = calibrate_penalties(mu, cov, risk_aversion=1.0, penalty_multiplier=2.0)
    assert pytest.approx(penalty_A, abs=1e-5) == 1.92
    assert pytest.approx(swing_bound, abs=1e-5) == 0.96


def test_build_qubo_matrix_shape():
    """Verify QUBO matrix dimensions and info fields."""
    mu = np.array([0.10, 0.15, 0.20, 0.25])
    cov = np.diag([0.04, 0.05, 0.06, 0.07])
    meta = pd.DataFrame({"Ticker": ["A", "B", "C", "D"], "Sector": ["S1", "S1", "S2", "S2"]})

    Q, offset, info = build_qubo_matrix(mu, cov, k_target=2, metadata_df=meta)
    
    assert Q.shape == (4, 4)
    assert info["k_target"] == 2
    assert info["penalty_A"] > 0
    assert info["penalty_B"] > 0
    assert sum(info["sector_targets"].values()) == 2
