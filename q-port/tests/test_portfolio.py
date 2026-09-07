"""
Unit tests for Stage-B continuous portfolio allocation module.
"""

import pytest
import numpy as np
import pandas as pd
from core.portfolio import optimize_continuous_weights


def test_stage_b_allocation_constraints():
    """Verify Stage-B SLSQP continuous weights respect capital, max weight, and sector limits."""
    mu = np.array([0.15, 0.20, 0.25, 0.30])
    cov = np.diag([0.04, 0.05, 0.06, 0.07])
    meta = pd.DataFrame({"Ticker": ["A", "B", "C", "D"], "Sector": ["S1", "S1", "S2", "S2"]})
    
    # Select 3 assets: A, B, C (indices 0, 1, 2)
    x = np.array([1, 1, 1, 0])
    max_weight = 0.50
    max_sector_weight = 0.60

    stats = optimize_continuous_weights(
        selection_vector=x,
        expected_returns=mu,
        cov_matrix=cov,
        max_weight=max_weight,
        max_sector_weight=max_sector_weight,
        metadata_df=meta
    )

    w = stats["weights"]
    
    # 1. Total capital allocated must equal 100%
    assert pytest.approx(np.sum(w), abs=1e-6) == 1.0
    
    # 2. Unselected asset D (index 3) must have weight 0
    assert w[3] == 0.0

    # 3. Individual asset max weight constraint
    assert np.all(w <= max_weight + 1e-6)

    # 4. Sector weight constraints (S1: A+B <= 0.60, S2: C <= 0.60)
    s1_weight = w[0] + w[1]
    s2_weight = w[2]
    assert s1_weight <= max_sector_weight + 1e-5
    assert s2_weight <= max_sector_weight + 1e-5
