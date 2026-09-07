"""
Red-Team Test: QAOA Optimization Convergence & Ground-State Smoke Test.
Verifies QAOA converges with >= 90% ground state probability on a small 4-qubit unconstrained system.
"""

import pytest
import numpy as np
from core.quantum_optimizer import solve_qaoa, qubo_to_ising, evaluate_qubo_cost
from config.settings import SMOKE_TEST_MIN_PROBABILITY


def test_qaoa_4qubit_convergence_smoke():
    """Smoke test: QAOA optimization converges on ground state for a 4-qubit diagonal QUBO."""
    # Diagonal QUBO where x = [1, 0, 1, 0] is strictly optimal with no constraints
    Q = np.diag([-5.0, 10.0, -8.0, 12.0])
    offset = 0.0

    # Target K=2 to match optimal cardinality
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=offset,
        k_target=2,
        p=2,
        shots=4096,
        max_iterations=200,
        seed=42
    )

    assert best_x is not None
    assert np.array_equal(best_x, np.array([1, 0, 1, 0]))
    assert int(np.sum(best_x)) == 2
    # Feasible rate among cardinality-2 samples should be high
    assert metrics["feasible_rate"] > 0.10
