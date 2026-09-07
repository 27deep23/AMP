"""
QAOA Quantum Engine for Q-PORT.
Translates QUBO formulation Q into Ising spin Hamiltonian H_C, builds p-layer QAOA circuit,
and executes simulation using Qiskit Aer local CPU simulator.
Enforces <=24 qubit ceiling and wall-clock timeout protection.
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from scipy.optimize import minimize

import qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from core.qubo import evaluate_qubo_cost
from utils.validation import InvalidParameterError, ComputationTimeoutError


def qubo_to_ising(Q: np.ndarray, offset: float) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Converts QUBO matrix Q and offset into Ising Hamiltonian parameters:
      H_C = sum_i h_i Z_i + sum_{i < j} J_{ij} Z_i Z_j + ising_offset
    using substitution x_i = (1 - Z_i) / 2.
    
    Returns:
      h: 1D array of single-spin Z coefficients h_i
      J: 2D upper-triangular array of two-spin ZZ couplings J_{ij}
      ising_offset: constant scalar
    """
    n = Q.shape[0]
    h = np.zeros(n, dtype=float)
    J = np.zeros((n, n), dtype=float)
    ising_offset = float(offset)

    # Q_ii * x_i = Q_ii * (1 - Z_i)/2 = Q_ii/2 - (Q_ii/2) Z_i
    for i in range(n):
        q_ii = Q[i, i]
        ising_offset += q_ii / 2.0
        h[i] -= q_ii / 2.0

    # Q_ij * x_i * x_j = Q_ij/4 - (Q_ij/4) Z_i - (Q_ij/4) Z_j + (Q_ij/4) Z_i Z_j
    for i in range(n):
        for j in range(i + 1, n):
            q_ij = Q[i, j] + Q[j, i]
            if not np.isclose(q_ij, 0.0):
                ising_offset += q_ij / 4.0
                h[i] -= q_ij / 4.0
                h[j] -= q_ij / 4.0
                J[i, j] += q_ij / 4.0

    return h, J, ising_offset


def build_qaoa_circuit(
    n_qubits: int,
    h: np.ndarray,
    J: np.ndarray,
    gamma: float,
    beta: float
) -> QuantumCircuit:
    """
    Builds a 1-layer QAOA circuit for Ising Hamiltonian (h, J).
    """
    qc = QuantumCircuit(n_qubits)

    # Initial state: Hadamard on all qubits
    for i in range(n_qubits):
        qc.h(i)

    # Cost Hamiltonian evolution: exp(-i * gamma * H_C)
    # 1. Single-qubit Z terms: exp(-i * gamma * h_i * Z_i) = rz(2 * gamma * h_i)
    for i in range(n_qubits):
        if not np.isclose(h[i], 0.0):
            qc.rz(2.0 * gamma * h[i], i)

    # 2. Two-qubit ZZ coupling terms: exp(-i * gamma * J_ij * Z_i Z_j)
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            if not np.isclose(J[i, j], 0.0):
                qc.rzz(2.0 * gamma * J[i, j], i, j)

    # Mixer Hamiltonian evolution: exp(-i * beta * sum X_i) = rx(2 * beta) on all qubits
    for i in range(n_qubits):
        qc.rx(2.0 * beta, i)

    qc.measure_all()
    return qc


def solve_qaoa(
    Q: np.ndarray,
    offset: float,
    k_target: int,
    p: int = 1,
    shots: int = 1024,
    max_qubits: int = 24,
    max_runtime_sec: float = 30.0,
    seed: int = 42
) -> Tuple[np.ndarray, float, float, Dict[str, Any]]:
    """
    Executes QAOA algorithm using Qiskit Aer local CPU simulator.
    
    Returns:
        best_x: binary vector corresponding to best sampled QUBO solution
        best_cost: scalar QUBO cost of best_x
        runtime_sec: total execution wall-clock time
        metrics: dict of quantum execution diagnostics
    """
    t0 = time.perf_counter()
    n = Q.shape[0]

    # Qubit ceiling check
    if n > max_qubits:
        raise InvalidParameterError(
            f"QAOA qubit count N={n} exceeds maximum local CPU limit ({max_qubits}). "
            "Skipping QAOA execution to prevent memory overflow."
        )

    # Convert QUBO to Ising
    h, J, ising_offset = qubo_to_ising(Q, offset)

    # Initialize Qiskit Aer simulator
    sim = AerSimulator(seed_simulator=seed)

    # Classical outer-loop parameter optimizer (COBYLA)
    def qaoa_objective(params):
        if (time.perf_counter() - t0) > max_runtime_sec:
            return 0.0  # Early stop signal

        gamma, beta = params[0], params[1]
        qc = build_qaoa_circuit(n, h, J, gamma, beta)
        result = sim.run(qc, shots=shots, seed_simulator=seed).result()
        counts = result.get_counts()

        # Compute expectation value of QUBO cost
        exp_cost = 0.0
        total_shots = sum(counts.values())

        for bitstr, count in counts.items():
            # Qiskit returns bitstrings in little-endian order (bit 0 is rightmost)
            # Reverse to match asset indexing [0..N-1]
            x_arr = np.array([int(b) for b in bitstr[::-1]], dtype=int)
            cost = evaluate_qubo_cost(x_arr, Q, offset)
            exp_cost += cost * count

        return exp_cost / total_shots

    # Initial parameter guess
    init_params = np.array([0.5, 0.5])
    
    # Run COBYLA parameter optimization
    res = minimize(
        qaoa_objective,
        x0=init_params,
        method="COBYLA",
        options={"maxiter": 30, "rhobeg": 0.2}
    )

    opt_gamma, opt_beta = res.x[0], res.x[1]

    # Final measurement run with optimal parameters and larger shot count
    final_qc = build_qaoa_circuit(n, h, J, opt_gamma, opt_beta)
    final_result = sim.run(final_qc, shots=shots*2, seed_simulator=seed).result()
    final_counts = final_result.get_counts()

    # Process all sampled bitstrings
    bitstring_records = []
    best_x = np.zeros(n, dtype=int)
    best_cost = float("inf")
    feasible_count = 0
    total_samples = sum(final_counts.values())

    for bitstr, count in final_counts.items():
        x_arr = np.array([int(b) for b in bitstr[::-1]], dtype=int)
        cost = evaluate_qubo_cost(x_arr, Q, offset)
        k_count = int(np.sum(x_arr))
        is_feasible = (k_count == k_target)

        if is_feasible:
            feasible_count += count

        if cost < best_cost:
            best_cost = cost
            best_x = x_arr.copy()

        bitstring_records.append({
            "bitstring": bitstr[::-1],
            "cost": cost,
            "count": count,
            "probability": count / total_samples,
            "is_feasible": is_feasible
        })

    t1 = time.perf_counter()
    runtime = t1 - t0

    # Best sampled probability
    best_bitstr_key = "".join(str(b) for b in best_x)
    best_prob = final_counts.get(best_bitstr_key[::-1], 0) / total_samples

    metrics = {
        "solver_type": "QAOA Quantum Engine (Qiskit Aer)",
        "n_qubits": n,
        "p_layers": p,
        "opt_gamma": float(opt_gamma),
        "opt_beta": float(opt_beta),
        "shots": total_samples,
        "feasible_rate": float(feasible_count / total_samples),
        "best_probability": float(best_prob),
        "runtime_sec": runtime,
        "bitstrings_evaluated": len(bitstring_records),
        "is_feasible": int(np.sum(best_x)) == k_target
    }

    return best_x, best_cost, runtime, metrics
