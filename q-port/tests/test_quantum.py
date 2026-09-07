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
    
    assert best_x is not None
    assert len(best_x) == 2
    assert int(np.sum(best_x)) == 1
    assert metrics["feasible_rate"] > 0.0
    assert metrics["best_probability"] >= 0.40
    assert metrics["solver_type"] == "QAOA Quantum Engine (Qiskit Aer)"


def test_qubit_ceiling_enforcement():
    """Verify QAOA refuses execution if N > 24 qubits."""
    dummy_Q = np.zeros((25, 25))
    with pytest.raises(InvalidParameterError) as exc_info:
        solve_qaoa(dummy_Q, offset=0.0, k_target=5, max_qubits=24)
    assert "exceeds maximum local CPU ceiling" in str(exc_info.value)


def test_hardware_provider_banned():
    """Verify qiskit-ibm-runtime is NOT installed / banned from Q-PORT."""
    with pytest.raises(ImportError):
        import qiskit_ibm_runtime


def test_qaoa_4qubit_convergence_smoke():
    """Smoke test: QAOA optimization converges on ground state for a 4-qubit diagonal QUBO with >= 90% probability."""
    # Strictly non-degenerate diagonal QUBO: x* = [0, 1, 0, 1] has unique minimum cost -4.0 among all K=2 candidates (others are >= 0.0)
    Q = np.diag([2.0, -2.0, 2.0, -2.0])
    offset = 0.0

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
    assert metrics["best_probability"] >= 0.90


def test_spsa_optimizer_execution_path():
    """Verify QAOA executes genuine SPSA optimizer path and records metrics."""
    Q = np.diag([1.0, -2.0, 1.0, -2.0])
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=0.0,
        k_target=2,
        optimizer_name="SPSA",
        max_iterations=10,
        seed=42
    )
    assert metrics["optimizer_name"] == "SPSA"
    assert metrics["configured_max_iterations"] == 10
    assert "actual_optimizer_iterations" in metrics


def test_stage_b_raw_slsqp_no_normalization():
    """Verify Stage-B accepts raw SLSQP solution without normalizing or clipping."""
    from core.portfolio import optimize_continuous_weights
    mu = np.array([0.15, 0.25])
    cov = np.diag([0.04, 0.09])
    st = optimize_continuous_weights(
        selection_vector=np.array([1, 1]),
        expected_returns=mu,
        cov_matrix=cov,
        risk_aversion=1.0,
        max_weight=0.80
    )
    assert st["stage_b_success"] is True
    assert abs(np.sum(st["weights"]) - 1.0) <= 1e-6
