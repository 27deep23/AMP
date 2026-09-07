"""
QAOA Quantum Engine for Q-PORT.
Translates QUBO formulation Q into Ising spin Hamiltonian H_C, builds genuine p-layer QAOA circuit
with 2p parameters [gamma_1, beta_1, ..., gamma_p, beta_p], and executes simulation using Qiskit Aer.
Enforces strict feasible-only candidate filtering (sum x_i == K), deadline-based timeout,
and <=24 qubit ceiling enforcement.
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
    gammas: np.ndarray,
    betas: np.ndarray
) -> QuantumCircuit:
    """
    Builds a genuine p-layer QAOA circuit for Ising Hamiltonian (h, J).
    `gammas` and `betas` must be 1D arrays of length p.
    """
    p = len(gammas)
    if len(betas) != p:
        raise ValueError(f"Length of gammas ({p}) and betas ({len(betas)}) must match.")

    qc = QuantumCircuit(n_qubits)

    # Initial state: Hadamard on all qubits (|=>^N)
    for i in range(n_qubits):
        qc.h(i)

    # Apply p alternating QAOA layers
    for layer in range(p):
        gamma_k = float(gammas[layer])
        beta_k = float(betas[layer])

        # 1. Cost Hamiltonian evolution: exp(-i * gamma_k * H_C)
        # Single-qubit Z terms: exp(-i * gamma_k * h_i * Z_i) = rz(2 * gamma_k * h_i)
        for i in range(n_qubits):
            if not np.isclose(h[i], 0.0):
                qc.rz(2.0 * gamma_k * h[i], i)

        # Two-qubit ZZ coupling terms: exp(-i * gamma_k * J_ij * Z_i Z_j) = rzz(2 * gamma_k * J_ij)
        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                if not np.isclose(J[i, j], 0.0):
                    qc.rzz(2.0 * gamma_k * J[i, j], i, j)

        # 2. Mixer Hamiltonian evolution: exp(-i * beta_k * sum X_i) = rx(2 * beta_k) on all qubits
        for i in range(n_qubits):
            qc.rx(2.0 * beta_k, i)

    qc.measure_all()
    return qc


def solve_qaoa(
    Q: np.ndarray,
    offset: float,
    k_target: int,
    p: int = 1,
    shots: int = 1024,
    max_iterations: int = 200,
    optimizer_name: str = "COBYLA",
    max_qubits: int = 24,
    max_runtime_sec: float = 30.0,
    seed: int = 42
) -> Tuple[Optional[np.ndarray], Optional[float], float, Dict[str, Any]]:
    """
    Executes genuine p-layer QAOA algorithm using Qiskit Aer local CPU simulator.
    Uses 2p parameters [gamma_1, beta_1, ..., gamma_p, beta_p].
    Enforces strict feasible-only candidate selection (sum x_i == K) and deadline-based timeout model.
    """
    t0 = time.perf_counter()
    deadline = t0 + max_runtime_sec
    n = Q.shape[0]

    # Qubit ceiling check
    if n > max_qubits:
        raise InvalidParameterError(
            f"QAOA qubit count N={n} exceeds maximum local CPU ceiling ({max_qubits}). "
            "Skipping QAOA execution to prevent local CPU memory overflow."
        )

    # Convert QUBO to Ising
    h, J, ising_offset = qubo_to_ising(Q, offset)

    # Initialize Qiskit Aer simulator
    sim = AerSimulator(seed_simulator=seed)

    # Parameter vector length = 2 * p: [gamma_1, beta_1, ..., gamma_p, beta_p]
    n_parameters = 2 * p

    eval_count = 0
    timed_out = False

    # Classical outer-loop objective: expected QUBO cost
    def qaoa_objective(params):
        nonlocal eval_count, timed_out
        eval_count += 1

        if time.perf_counter() >= deadline:
            timed_out = True
            return 0.0  # Abort optimization loop

        gammas = params[0::2]
        betas = params[1::2]

        qc = build_qaoa_circuit(n, h, J, gammas, betas)
        result = sim.run(qc, shots=shots, seed_simulator=seed).result()
        counts = result.get_counts()

        # Expectation value of QUBO cost
        exp_cost = 0.0
        tot_shots = sum(counts.values())

        for bitstr, count in counts.items():
            # Qiskit bitstrings are little-endian (bit 0 rightmost)
            x_arr = np.array([int(b) for b in bitstr[::-1]], dtype=int)
            cost = evaluate_qubo_cost(x_arr, Q, offset)
            exp_cost += cost * count

        return exp_cost / tot_shots

    # Initial parameter guess: [0.5, 0.5] repeated p times
    init_params = np.tile([0.5, 0.5], p)

    # Choose outer-loop optimizer: genuine COBYLA or SPSA
    opt_name = optimizer_name.upper()
    if opt_name == "SPSA":
        # Genuine Simultaneous Perturbation Stochastic Approximation (SPSA)
        rng_spsa = np.random.default_rng(seed)
        best_params = init_params.copy().astype(float)
        p_len = len(best_params)
        spsa_a = 0.1
        spsa_c = 0.1
        spsa_A = max(10, int(0.1 * max_iterations))

        for k_iter in range(max_iterations):
            if time.perf_counter() >= deadline:
                timed_out = True
                break
            ak = spsa_a / ((k_iter + 1 + spsa_A) ** 0.602)
            ck = spsa_c / ((k_iter + 1) ** 0.101)
            delta = rng_spsa.choice([-1.0, 1.0], size=p_len)
            x_plus = best_params + ck * delta
            x_minus = best_params - ck * delta
            f_plus = qaoa_objective(x_plus)
            f_minus = qaoa_objective(x_minus)
            ghat = (f_plus - f_minus) / (2.0 * ck * delta)
            best_params = best_params - ak * ghat
    else:
        # Default COBYLA
        res = minimize(
            qaoa_objective,
            x0=init_params,
            method="COBYLA",
            options={"maxiter": max_iterations}
        )
        best_params = res.x

    opt_gammas = best_params[0::2]
    opt_betas = best_params[1::2]

    # Pre-final measurement deadline check
    if time.perf_counter() >= deadline:
        timed_out = True

    if not timed_out:
        # Final measurement execution with optimal parameters using EXACT requested shots (NO shots * 2)
        final_qc = build_qaoa_circuit(n, h, J, opt_gammas, opt_betas)
        final_result = sim.run(final_qc, shots=shots, seed_simulator=seed).result()
        final_counts = final_result.get_counts()

        if time.perf_counter() >= deadline:
            timed_out = True
    else:
        final_counts = {}

    t1 = time.perf_counter()
    runtime = t1 - t0

    # Post-Aer deadline check
    if runtime >= max_runtime_sec or timed_out:
        timed_out = True
        metrics = {
            "solver_type": "QAOA Quantum Engine (Qiskit Aer)",
            "actual_qaoa_p": p,
            "actual_parameter_count": n_parameters,
            "configured_max_iterations": max_iterations,
            "actual_optimizer_iterations": eval_count,
            "optimizer_name": optimizer_name,
            "n_qubits": n,
            "opt_gammas": [float(g) for g in opt_gammas],
            "opt_betas": [float(b) for b in opt_betas],
            "optimization_shots": shots,
            "final_measurement_shots": shots,
            "shots": shots,
            "feasible_rate": 0.0,
            "best_probability": 0.0,
            "runtime_sec": runtime,
            "status": "timeout",
            "is_feasible": False
        }
        return None, None, runtime, metrics

    if not timed_out and len(final_counts) > 0:
        # Process all sampled bitstrings and filter for FEASIBLE candidates ONLY (sum x_i == K)
        best_feasible_x = None
        best_feasible_cost = float("inf")
        feasible_count = 0
        total_samples = sum(final_counts.values())

        for bitstr, count in final_counts.items():
            x_arr = np.array([int(b) for b in bitstr[::-1]], dtype=int)
            cost = evaluate_qubo_cost(x_arr, Q, offset)
            k_count = int(np.sum(x_arr))
            is_feasible = (k_count == k_target)

            if is_feasible:
                feasible_count += count
                if cost < best_feasible_cost:
                    best_feasible_cost = cost
                    best_feasible_x = x_arr.copy()

        feasible_rate = float(feasible_count / total_samples) if total_samples > 0 else 0.0

        if best_feasible_x is not None:
            best_bitstr_key = "".join(str(b) for b in best_feasible_x)
            best_prob = float(final_counts.get(best_bitstr_key[::-1], 0) / total_samples) if total_samples > 0 else 0.0
            status = "success"
            best_x = best_feasible_x
            best_cost = best_feasible_cost
        else:
            best_prob = 0.0
            status = "no_feasible_solution"
            best_x = None
            best_cost = None
    else:
        feasible_rate = 0.0
        best_prob = 0.0
        status = "timeout" if timed_out else "no_feasible_solution"
        best_x = None
        best_cost = None

    metrics = {
        "solver_type": "QAOA Quantum Engine (Qiskit Aer)",
        "actual_qaoa_p": p,
        "actual_parameter_count": n_parameters,
        "configured_max_iterations": max_iterations,
        "actual_optimizer_iterations": eval_count,
        "optimizer_name": optimizer_name,
        "n_qubits": n,
        "opt_gammas": [float(g) for g in opt_gammas],
        "opt_betas": [float(b) for b in opt_betas],
        "optimization_shots": shots,
        "final_measurement_shots": shots,
        "shots": shots,
        "feasible_rate": feasible_rate,
        "best_probability": best_prob,
        "runtime_sec": runtime,
        "status": status,
        "is_feasible": best_x is not None
    }

    return best_x, best_cost, runtime, metrics
