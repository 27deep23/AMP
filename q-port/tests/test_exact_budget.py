"""
Unit tests for exact enumeration solver and budget ceilings.
"""

import pytest
import numpy as np
import pandas as pd
from core.qubo import build_qubo_matrix, evaluate_qubo_cost
from core.classical_optimizer import solve_exact_enumeration, solve_greedy, solve_simulated_annealing
from utils.validation import InvalidParameterError


def test_exact_enumeration_global_optimum():
    """Verify exact enumeration finds global minimum on small N=8 instance."""
    mu = np.array([0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28])
    cov = np.diag([0.04, 0.05, 0.045, 0.06, 0.055, 0.07, 0.065, 0.08])
    meta = pd.DataFrame({"Ticker": [f"T{i}" for i in range(8)], "Sector": ["S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4"]})

    Q, offset, info = build_qubo_matrix(mu, cov, k_target=3, metadata_df=meta)

    best_x, best_cost, runtime, metrics = solve_exact_enumeration(Q, offset, k_target=3)

    assert metrics["is_exact"] is True
    assert metrics["solver_type"] == "Exact Enumeration (Classical Brute-Force)"
    assert int(np.sum(best_x)) == 3

    # Manual verification over all combinations C(8, 3) = 56
    import itertools
    min_manual = float("inf")
    for combo in itertools.combinations(range(8), 3):
        x = np.zeros(8, dtype=int)
        x[list(combo)] = 1
        c = evaluate_qubo_cost(x, Q, offset)
        if c < min_manual:
            min_manual = c

    assert pytest.approx(best_cost, abs=1e-8) == min_manual


def test_exact_enumeration_state_count_ceiling():
    """Verify exact solver raises InvalidParameterError if total states > 2^22 limit."""
    # N=30, K=15 => C(30, 15) = 155,117,520 > 2^22 (4,194,304)
    dummy_Q = np.zeros((30, 30))
    with pytest.raises(InvalidParameterError) as exc_info:
        solve_exact_enumeration(dummy_Q, offset=0.0, k_target=15, max_state_count=2**22)
    assert "exceeds maximum allowed limit" in str(exc_info.value)
