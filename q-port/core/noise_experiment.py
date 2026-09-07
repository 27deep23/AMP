"""
Simulated Noise Sensitivity Experiment for Q-PORT.
Compares ideal QAOA execution against noisy QAOA simulation (using depolarizing noise models)
to assess quantum algorithm robustness under simulated hardware decoherence.
"""

import numpy as np
from typing import Dict, Any, Tuple
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from core.quantum_optimizer import build_qaoa_circuit, qubo_to_ising
from core.qubo import evaluate_qubo_cost


def run_noise_sensitivity_experiment(
    Q: np.ndarray,
    offset: float,
    k_target: int,
    depolarizing_p1: float = 0.01,
    depolarizing_p2: float = 0.03,
    shots: int = 1024,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs ideal vs noisy QAOA simulation.
    
    Returns:
        Dict containing ideal_metrics, noisy_metrics, and noise_model_info.
    """
    n = Q.shape[0]
    h, J, _ = qubo_to_ising(Q, offset)

    # 1. Ideal Simulator
    sim_ideal = AerSimulator(seed_simulator=seed)
    qc = build_qaoa_circuit(n, h, J, gamma=0.5, beta=0.5)
    
    res_ideal = sim_ideal.run(qc, shots=shots, seed_simulator=seed).result()
    counts_ideal = res_ideal.get_counts()

    # 2. Noisy Simulator with Depolarizing Noise Model
    noise_model = NoiseModel()
    error_1q = depolarizing_error(depolarizing_p1, 1)
    error_2q = depolarizing_error(depolarizing_p2, 2)
    noise_model.add_all_qubit_quantum_error(error_1q, ["rz", "rx", "h"])
    noise_model.add_all_qubit_quantum_error(error_2q, ["rzz", "cx"])

    sim_noisy = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    res_noisy = sim_noisy.run(qc, shots=shots, seed_simulator=seed).result()
    counts_noisy = res_noisy.get_counts()

    # Calculate feasible rates and best costs for both
    def analyze_counts(counts):
        feasible_count = 0
        best_c = float("inf")
        tot = sum(counts.values())
        for bstr, cnt in counts.items():
            x = np.array([int(b) for b in bstr[::-1]], dtype=int)
            c = evaluate_qubo_cost(x, Q, offset)
            if int(np.sum(x)) == k_target:
                feasible_count += cnt
            if c < best_c:
                best_c = c
        return float(feasible_count / tot), float(best_c)

    feas_ideal, cost_ideal = analyze_counts(counts_ideal)
    feas_noisy, cost_noisy = analyze_counts(counts_noisy)

    return {
        "disclaimer": "Simulated noise sensitivity experiment (aer_simulator + depolarizing noise model)",
        "p1_single_qubit_error": depolarizing_p1,
        "p2_two_qubit_error": depolarizing_p2,
        "ideal_feasible_rate": feas_ideal,
        "noisy_feasible_rate": feas_noisy,
        "ideal_best_cost": cost_ideal,
        "noisy_best_cost": cost_noisy,
        "fidelity_drop_pct": float((feas_ideal - feas_noisy) * 100.0)
    }
