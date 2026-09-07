"""
Red-Team Test: QUBO <-> Ising Mathematical Equivalence.
Verifies exact match between QUBO cost x^T Q x + c and Ising spin expectation value <z|H_Ising|z>.
"""

import pytest
import numpy as np
from core.qubo import evaluate_qubo_cost
from core.quantum_optimizer import qubo_to_ising


def test_qubo_ising_100_configs_equivalence():
    """Verify QUBO and Ising costs match across 100 random bitstring configurations."""
    np.random.seed(123)
    N = 6
    A = np.random.randn(N, N)
    Q = 0.5 * (A + A.T)
    offset = -3.14159

    h, J, ising_offset = qubo_to_ising(Q, offset)

    for _ in range(100):
        x = np.random.randint(0, 2, size=N)
        qubo_cost = evaluate_qubo_cost(x, Q, offset)

        # Spin mapping: z_i = 1 - 2*x_i  => x_i = (1 - z_i)/2
        z = 1.0 - 2.0 * x

        # Ising energy: sum_i h_i z_i + sum_{i<j} J_{ij} z_i z_j + ising_offset
        ising_cost = float(np.dot(h, z) + np.sum(np.triu(J, k=1) * np.outer(z, z)) + ising_offset)

        assert abs(qubo_cost - ising_cost) < 1e-8
