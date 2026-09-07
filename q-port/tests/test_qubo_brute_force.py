"""
Red-Team Test: Standalone N=8 Brute-Force QUBO Verification.
Evaluates all 256 binary vectors against evaluate_qubo_cost and explicit matrix product x^T Q x + offset.
"""

import pytest
import numpy as np
import itertools
from core.qubo import evaluate_qubo_cost


def test_qubo_n8_brute_force_exactness():
    """Verify QUBO cost evaluation across all 256 states for N=8."""
    np.random.seed(42)
    N = 8
    A = np.random.randn(N, N)
    Q = 0.5 * (A + A.T)  # Symmetric matrix
    offset = 12.345

    min_manual_cost = float("inf")
    min_manual_x = None

    min_eval_cost = float("inf")
    min_eval_x = None

    for bits in itertools.product([0, 1], repeat=N):
        x = np.array(bits, dtype=float)

        # Manual evaluation: x^T Q x + offset
        manual_cost = float(np.dot(x, np.dot(Q, x)) + offset)

        # Module evaluation
        eval_cost = evaluate_qubo_cost(x.astype(int), Q, offset)

        assert abs(manual_cost - eval_cost) < 1e-10

        if manual_cost < min_manual_cost:
            min_manual_cost = manual_cost
            min_manual_x = x

        if eval_cost < min_eval_cost:
            min_eval_cost = eval_cost
            min_eval_x = x

    assert abs(min_manual_cost - min_eval_cost) < 1e-10
    assert np.array_equal(min_manual_x, min_eval_x)
