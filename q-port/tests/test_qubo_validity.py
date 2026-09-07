"""
Brute-force validity test for QUBO formulation.
Evaluates random binary vectors x on both x^T Q x + offset and direct objective C(x),
asserting numerical agreement to within 1e-10.
"""

import pytest
import numpy as np
import pandas as pd
from core.data_loader import fetch_market_data
from core.preprocessing import preprocess_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix, evaluate_qubo_cost, evaluate_direct_objective


def test_qubo_numerical_validity():
    """
    Brute-force test: Compares x^T Q x + offset vs direct C(x) across 500 random binary vectors.
    Must agree to within 1e-10.
    """
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)
    
    # Subset to 15 assets
    returns_df = returns_df.iloc[:, :15]
    clean_meta = clean_meta.iloc[:15]
    
    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)
    n = len(mu)
    k_target = 5
    risk_aversion = 1.2
    
    Q, offset, info = build_qubo_matrix(
        expected_returns=mu,
        cov_matrix=cov,
        k_target=k_target,
        risk_aversion=risk_aversion,
        metadata_df=clean_meta
    )
    
    A = info["penalty_A"]
    B = info["penalty_B"]
    
    np.random.seed(123)
    max_diff = 0.0

    # Evaluate 500 random binary bitstrings
    for _ in range(500):
        x = np.random.randint(0, 2, size=n)
        
        matrix_cost = evaluate_qubo_cost(x, Q, offset)
        direct_cost = evaluate_direct_objective(
            x=x,
            expected_returns=mu,
            cov_matrix=cov,
            k_target=k_target,
            risk_aversion=risk_aversion,
            penalty_A=A,
            penalty_B=B,
            metadata_df=clean_meta
        )
        
        diff = abs(matrix_cost - direct_cost)
        if diff > max_diff:
            max_diff = diff
            
        assert diff < 1e-10, f"Discrepancy detected for bitstring {x}: matrix={matrix_cost}, direct={direct_cost}, diff={diff}"

    print(f"Verified 500 binary vectors. Max difference: {max_diff:.2e}")
