"""
Unit tests for QAOA Quantum Engine (core/quantum_optimizer.py).
"""

import pytest
import numpy as np
from core.qubo import build_qubo_matrix, evaluate_qubo_cost
from core.quantum_optimizer import qubo_to_ising, solve_qaoa
from utils.validation import InvalidParameterError


def test_qubo_to_ising_conversion():
    """Verify QUBO matrix to Ising Hamiltonian parameter conversion."""
    Q = np.array([[2.0, 1.0], [1.0, 3.0]])
    offset = 0.5
    
    h, J, ising_offset = qubo_to_ising(Q, offset)
    
    assert len(h) == 2
    assert J.shape == (2, 2)
    # Check that Ising representation yields same value as QUBO for all spin configs
    for x in [[0, 0], [1, 0], [0, 1], [1, 1]]:
        x_vec = np.array(x)
        qubo_val = evaluate_qubo_cost(x_vec, Q, offset)
        
        # z_i = 1 - 2*x_i
        z = 1.0 - 2.0 * x_vec
        ising_val = np.dot(h, z) + z[0] * J[0, 1] * z[1] + ising_offset
        assert pytest.approx(qubo_val, abs=1e-8) == ising_val


def test_qaoa_2qubit_smoke_test():
    """Smoke test: 2-qubit QAOA finds optimal bitstring."""
    mu = np.array([0.10, 0.30])
    cov = np.diag([0.04, 0.09])
    
    Q, offset, info = build_qubo_matrix(mu, cov, k_target=1)
    
    best_x, best_cost, runtime, metrics = solve_qaoa(Q, offset, k_target=1, seed=42)
    
    assert len(best_x) == 2
    assert int(np.sum(best_x)) == 1
    assert metrics["feasible_rate"] > 0.0
    assert metrics["solver_type"] == "QAOA Quantum Engine (Qiskit Aer)"


def test_qubit_ceiling_enforcement():
    """Verify QAOA refuses execution if N > 24 qubits."""
    dummy_Q = np.zeros((25, 25))
    with pytest.raises(InvalidParameterError) as exc_info:
        solve_qaoa(dummy_Q, offset=0.0, k_target=5, max_qubits=24)
    assert "exceeds maximum local CPU limit" in str(exc_info.value)


def test_hardware_provider_banned():
    """Verify qiskit-ibm-runtime is NOT installed / banned from Q-PORT."""
    with pytest.raises(ImportError):
        import qiskit_ibm_runtime
