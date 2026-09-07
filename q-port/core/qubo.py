"""
QUBO construction and penalty calibration engine for Q-PORT.
Formulates asset selection as a Quadratic Unconstrained Binary Optimization (QUBO) problem:
  C(x) = x^T Q x + offset
incorporating Markowitz proxy return/risk and integer cardinality & sector constraints.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from utils.validation import InvalidParameterError


def allocate_sector_targets(
    sector_list: List[str],
    k_target: int
) -> Dict[str, int]:
    """
    Allocates integer sector targets K_s using deterministic largest-remainder method so sum(K_s) == K.
    R_s = K * N_s / N
    """
    df_sec = pd.Series(sector_list)
    sector_counts = df_sec.value_counts()
    n_total = len(sector_list)

    if n_total == 0 or k_target == 0:
        return {}

    # Exact fractional targets R_s = K * N_s / N
    fractions = {sec: (count / n_total) * k_target for sec, count in sector_counts.items()}
    floors = {sec: int(np.floor(f)) for sec, f in fractions.items()}
    remainders = {sec: fractions[sec] - floors[sec] for sec in fractions}

    current_sum = sum(floors.values())
    shortfall = k_target - current_sum

    # Sort sectors by remainder descending
    sorted_by_rem = sorted(remainders.keys(), key=lambda s: remainders[s], reverse=True)

    k_sector = floors.copy()
    for i in range(shortfall):
        sec = sorted_by_rem[i % len(sorted_by_rem)]
        k_sector[sec] += 1

    return k_sector


def calibrate_penalties(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_aversion: float = 1.0,
    penalty_multiplier: float = 2.0
) -> Tuple[float, float]:
    """
    Calibrates penalty coefficients A and B based on the actual instance's objective swing bound:
      objective_swing_bound = max(|mu_i|) * N + lambda * max(eigenvalues(Sigma)) * N^2
      Penalty = multiplier * objective_swing_bound
    
    Returns:
      (penalty, objective_swing_bound)
    """
    n = len(expected_returns)
    if n == 0:
        return 1.0, 0.5

    max_abs_ret = float(np.max(np.abs(expected_returns)))
    
    if len(cov_matrix) > 0 and cov_matrix.shape[0] == n:
        eigvals = np.linalg.eigvalsh(cov_matrix)
        max_eig = float(np.max(eigvals))
    else:
        max_eig = 0.1

    bound = (max_abs_ret * n) + (risk_aversion * max_eig * (n ** 2))
    bound = max(0.1, float(bound))
    penalty = penalty_multiplier * bound

    return float(penalty), bound


def build_qubo_matrix(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    k_target: int,
    risk_aversion: float = 1.0,
    penalty_a: Optional[float] = None,
    penalty_b: Optional[float] = None,
    penalty_multiplier: float = 2.0,
    metadata_df: Optional[pd.DataFrame] = None
) -> Tuple[np.ndarray, float, Dict[str, Any]]:
    """
    Builds the N x N QUBO matrix Q and scalar offset such that:
      C(x) = x^T Q x + offset
    
    Returns:
      Q: N x N upper-triangular or symmetric numpy matrix
      offset: scalar float constant
      qubo_info: Dict containing formulation details (K_target, A, B, sector targets, swing bound)
    """
    n = len(expected_returns)
    if n == 0:
        raise InvalidParameterError("Expected returns vector is empty.")

    if k_target < 1 or k_target > n:
        raise InvalidParameterError(f"Target K ({k_target}) must be between 1 and N ({n}).")

    # Calibrate penalties dynamically
    auto_penalty, swing_bound = calibrate_penalties(expected_returns, cov_matrix, risk_aversion, penalty_multiplier)

    is_manual_override = (penalty_a is not None or penalty_b is not None)
    A = float(penalty_a if penalty_a is not None else auto_penalty)
    B = float(penalty_b if penalty_b is not None else auto_penalty)

    # Sector target allocation
    sector_targets = {}
    sector_list = []
    if metadata_df is not None and "Sector" in metadata_df.columns:
        sector_list = metadata_df["Sector"].tolist()
        sector_targets = allocate_sector_targets(sector_list, k_target)

    # Initialize Q matrix and offset
    Q = np.zeros((n, n), dtype=float)
    offset = 0.0

    # 1. Financial Objective: - (mu^T x / K - lambda * x^T Sigma x / K^2)
    # Linear return terms: - mu_i / K
    for i in range(n):
        Q[i, i] += - expected_returns[i] / k_target

    # Quadratic risk terms: + lambda * Sigma_ij / K^2
    for i in range(n):
        for j in range(n):
            Q[i, j] += risk_aversion * cov_matrix[i, j] / (k_target ** 2)

    # 2. Cardinality Constraint Penalty: A * (sum_i x_i - K)^2
    # (sum x_i - K)^2 = sum_i (1 - 2 K) x_i + 2 * sum_{i < j} x_i x_j + K^2
    for i in range(n):
        Q[i, i] += A * (1.0 - 2.0 * k_target)
    for i in range(n):
        for j in range(i + 1, n):
            Q[i, j] += 2.0 * A
    offset += A * (k_target ** 2)

    # 3. Sector Constraint Penalties: B * sum_s (sum_{i in s} x_i - K_s)^2
    if sector_targets and len(sector_list) == n:
        for sec, k_s in sector_targets.items():
            sec_indices = [idx for idx, s in enumerate(sector_list) if s == sec]
            for i in sec_indices:
                Q[i, i] += B * (1.0 - 2.0 * k_s)
            for i_pos, i in enumerate(sec_indices):
                for j in sec_indices[i_pos + 1:]:
                    Q[i, j] += 2.0 * B
            offset += B * (k_s ** 2)

    qubo_info = {
        "n_assets": n,
        "k_target": k_target,
        "risk_aversion": risk_aversion,
        "objective_swing_bound": swing_bound,
        "penalty_multiplier": penalty_multiplier,
        "auto_penalty": auto_penalty,
        "penalty_A": A,
        "penalty_B": B,
        "is_manual_override": is_manual_override,
        "sector_targets": sector_targets,
        "offset": offset
    }

    return Q, offset, qubo_info


def evaluate_qubo_cost(x: np.ndarray, Q: np.ndarray, offset: float) -> float:
    """Evaluates cost C(x) = x^T Q x + offset for binary vector x."""
    x_vec = np.asarray(x, dtype=float)
    return float(np.dot(x_vec, np.dot(Q, x_vec)) + offset)


def evaluate_direct_objective(
    x: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    k_target: int,
    risk_aversion: float,
    penalty_A: float,
    penalty_B: float,
    metadata_df: Optional[pd.DataFrame] = None
) -> float:
    """Evaluates direct mathematical cost function C(x) without matrix Q."""
    x_vec = np.asarray(x, dtype=float)
    k_selected = np.sum(x_vec)

    # Markowitz proxy
    proxy_ret = np.dot(expected_returns, x_vec) / k_target
    proxy_risk = np.dot(x_vec, np.dot(cov_matrix, x_vec)) / (k_target ** 2)
    fin_obj = - (proxy_ret - risk_aversion * proxy_risk)

    # Cardinality penalty
    card_pen = penalty_A * ((k_selected - k_target) ** 2)

    # Sector penalty
    sec_pen = 0.0
    if metadata_df is not None and "Sector" in metadata_df.columns:
        sector_list = metadata_df["Sector"].tolist()
        sector_targets = allocate_sector_targets(sector_list, k_target)
        for sec, k_s in sector_targets.items():
            sec_count = sum(x_vec[idx] for idx, s in enumerate(sector_list) if s == sec)
            sec_pen += penalty_B * ((sec_count - k_s) ** 2)

    return float(fin_obj + card_pen + sec_pen)
