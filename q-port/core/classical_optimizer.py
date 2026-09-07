"""
Classical combinatorial solvers for Q-PORT:
1. Greedy Heuristic
2. Simulated Annealing (SA)
3. Exact Enumeration (Brute-Force) with dual state-count (2^22) and runtime (10s) budgets.
All operate on identical QUBO formulation Q and offset.
"""

import time
import math
import itertools
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from core.qubo import evaluate_qubo_cost
from utils.validation import ComputationTimeoutError, InvalidParameterError


def solve_greedy(
    Q: np.ndarray,
    offset: float,
    k_target: int
) -> Tuple[np.ndarray, float, float, Dict[str, Any]]:
    """
    Greedy heuristic solver.
    Starts with empty selection, iteratively picks the asset yielding lowest QUBO cost.
    
    Returns:
        best_x: binary vector of size N
        best_cost: scalar QUBO cost
        runtime_sec: execution time in seconds
        metrics: solver metadata
    """
    t0 = time.perf_counter()
    n = Q.shape[0]

    current_x = np.zeros(n, dtype=int)
    unselected = set(range(n))

    # Pick k_target assets greedily
    for _ in range(min(k_target, n)):
        best_candidate = -1
        best_cand_cost = float("inf")

        for idx in unselected:
            temp_x = current_x.copy()
            temp_x[idx] = 1
            cost = evaluate_qubo_cost(temp_x, Q, offset)
            if cost < best_cand_cost:
                best_cand_cost = cost
                best_candidate = idx

        if best_candidate != -1:
            current_x[best_candidate] = 1
            unselected.remove(best_candidate)

    # Local search step: try swapping 1 selected asset with 1 unselected asset
    improved = True
    while improved:
        improved = False
        selected_indices = np.where(current_x == 1)[0]
        unselected_indices = np.where(current_x == 0)[0]
        current_best_cost = evaluate_qubo_cost(current_x, Q, offset)

        for s_idx in selected_indices:
            for u_idx in unselected_indices:
                temp_x = current_x.copy()
                temp_x[s_idx] = 0
                temp_x[u_idx] = 1
                cost = evaluate_qubo_cost(temp_x, Q, offset)
                if cost < current_best_cost - 1e-8:
                    current_best_cost = cost
                    current_x = temp_x.copy()
                    improved = True
                    break
            if improved:
                break

    t1 = time.perf_counter()
    final_cost = evaluate_qubo_cost(current_x, Q, offset)
    runtime = t1 - t0

    metrics = {
        "solver_type": "Greedy Heuristic",
        "iterations": k_target,
        "runtime_sec": runtime,
        "is_feasible": int(np.sum(current_x)) == k_target
    }

    return current_x, final_cost, runtime, metrics


def solve_simulated_annealing(
    Q: np.ndarray,
    offset: float,
    k_target: int,
    t_initial: float = 10.0,
    t_min: float = 0.001,
    alpha: float = 0.98,
    max_steps: int = 5000,
    seed: int = 42
) -> Tuple[np.ndarray, float, float, Dict[str, Any]]:
    """
    Simulated Annealing solver on QUBO objective.
    
    Returns:
        best_x: binary vector of size N
        best_cost: scalar QUBO cost
        runtime_sec: execution time in seconds
        metrics: solver metadata
    """
    t0 = time.perf_counter()
    np.random.seed(seed)
    n = Q.shape[0]

    # Initial random solution with exactly k_target bits set
    current_x = np.zeros(n, dtype=int)
    init_indices = np.random.choice(n, size=min(k_target, n), replace=False)
    current_x[init_indices] = 1
    current_cost = evaluate_qubo_cost(current_x, Q, offset)

    best_x = current_x.copy()
    best_cost = current_cost

    t_curr = t_initial
    step = 0
    accepted_moves = 0

    while t_curr > t_min and step < max_steps:
        step += 1
        selected_indices = np.where(current_x == 1)[0]
        unselected_indices = np.where(current_x == 0)[0]

        if len(selected_indices) == 0 or len(unselected_indices) == 0:
            break

        # Propose bit swap
        s_idx = np.random.choice(selected_indices)
        u_idx = np.random.choice(unselected_indices)

        next_x = current_x.copy()
        next_x[s_idx] = 0
        next_x[u_idx] = 1

        next_cost = evaluate_qubo_cost(next_x, Q, offset)
        delta = next_cost - current_cost

        # Metropolis acceptance criterion
        if delta < 0 or np.random.rand() < math.exp(-delta / t_curr):
            current_x = next_x
            current_cost = next_cost
            accepted_moves += 1

            if current_cost < best_cost:
                best_cost = current_cost
                best_x = current_x.copy()

        t_curr *= alpha

    t1 = time.perf_counter()
    runtime = t1 - t0

    metrics = {
        "solver_type": "Simulated Annealing",
        "total_steps": step,
        "accepted_moves": accepted_moves,
        "runtime_sec": runtime,
        "is_feasible": int(np.sum(best_x)) == k_target
    }

    return best_x, best_cost, runtime, metrics


def solve_exact_enumeration(
    Q: np.ndarray,
    offset: float,
    k_target: int,
    max_state_count: int = 2**22,
    max_runtime_sec: float = 10.0
) -> Tuple[Optional[np.ndarray], Optional[float], float, Dict[str, Any]]:
    """
    Exact Enumeration (Classical Brute-Force) solver.
    Evaluates combinations C(N, K) with strict dual budget limits:
      - Max state count <= 2^22
      - Max wall-clock runtime <= 10.0s
    """
    t0 = time.perf_counter()
    n = Q.shape[0]

    # Calculate total combinations to evaluate
    num_combinations = math.comb(n, k_target)

    # Check state count ceiling
    if num_combinations > max_state_count:
        runtime = time.perf_counter() - t0
        metrics = {
            "solver_type": "Exact Enumeration (Classical Brute-Force)",
            "total_combinations": num_combinations,
            "evaluated_combinations": 0,
            "runtime_sec": runtime,
            "timed_out": False,
            "budget_exceeded_states": True,
            "is_exact": False,
            "is_feasible": False,
            "status": "state_count_budget_exceeded"
        }
        return None, None, runtime, metrics

    best_x = np.zeros(n, dtype=int)
    best_cost = float("inf")
    evaluated_count = 0
    timed_out = False

    # Iterate over all combinations of size k_target
    for combo in itertools.combinations(range(n), k_target):
        evaluated_count += 1
        
        # Check timeout every 5,000 evaluations
        if evaluated_count % 5000 == 0:
            if (time.perf_counter() - t0) > max_runtime_sec:
                timed_out = True
                break

        x = np.zeros(n, dtype=int)
        x[list(combo)] = 1
        cost = evaluate_qubo_cost(x, Q, offset)

        if cost < best_cost:
            best_cost = cost
            best_x = x.copy()

    t1 = time.perf_counter()
    runtime = t1 - t0

    is_exact = (not timed_out) and (evaluated_count == num_combinations)

    metrics = {
        "solver_type": "Exact Enumeration (Classical Brute-Force)",
        "total_combinations": num_combinations,
        "evaluated_combinations": evaluated_count,
        "runtime_sec": runtime,
        "timed_out": timed_out,
        "budget_exceeded_states": False,
        "is_exact": is_exact,
        "is_feasible": int(np.sum(best_x)) == k_target if best_x is not None else False,
        "status": "success" if is_exact else ("timeout" if timed_out else "incomplete")
    }

    return best_x, best_cost, runtime, metrics
