"""
Red-Team Test: QAOA Optimization Convergence & Ground-State Smoke Test.
Verifies QAOA converges with >= 90% ground state probability on a small 4-qubit unconstrained system.
"""

import pytest
import numpy as np
from core.quantum_optimizer import solve_qaoa, qubo_to_ising, evaluate_qubo_cost
from config.settings import SMOKE_TEST_MIN_PROBABILITY


def test_qaoa_4qubit_convergence_smoke():
    """Smoke test: QAOA optimization converges on ground state for a 4-qubit diagonal QUBO with >= 90% probability."""
    # Strictly non-degenerate diagonal QUBO: x* = [0, 1, 0, 1] has unique minimum cost -4.0 among all K=2 candidates (others are >= 0.0)
    Q = np.diag([2.0, -2.0, 2.0, -2.0])
    offset = 0.0

    # Target K=2 to match optimal cardinality (x* = [0, 1, 0, 1])
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=offset,
        k_target=2,
        p=1,
        shots=8192,
        max_iterations=100,
        seed=42
    )

    assert best_x is not None
    assert np.array_equal(best_x, [0, 1, 0, 1])
    assert int(np.sum(best_x)) == 2
    # Verify measured probability of known ground state meets >= 0.90
    assert metrics["best_probability"] >= SMOKE_TEST_MIN_PROBABILITY
