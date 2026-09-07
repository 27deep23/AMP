"""
Stage-B continuous portfolio allocation engine for Q-PORT.
Optimizes continuous weights w for a given asset selection vector x using SciPy SLSQP.
Provides identical Stage-B optimization for all solvers (QAOA, Greedy, SA, Exact).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from scipy.optimize import minimize
from core.statistics import compute_portfolio_stats


SUM_TOLERANCE: float = 1e-6
CONSTRAINT_TOLERANCE: float = 1e-6


def optimize_continuous_weights(
    selection_vector: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_aversion: float = 1.0,
    max_weight: float = 1.0,
    min_weight: float = 0.0,
    max_sector_weight: float = 1.0,
    target_return: Optional[float] = None,
    target_volatility: Optional[float] = None,
    returns_df: Optional[pd.DataFrame] = None,
    metadata_df: Optional[pd.DataFrame] = None,
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """
    Stage B continuous optimization over selected assets (where x_i = 1).
    
    Returns:
        Dict containing full continuous weight vector w (size N), optimized stats, and status.
    """
    x = np.asarray(selection_vector, dtype=int)
    n_total = len(x)
    selected_indices = np.where(x == 1)[0]
    k_selected = len(selected_indices)

    full_weights = np.zeros(n_total, dtype=float)

    if k_selected == 0:
        # No assets selected -> return zero weights
        return compute_portfolio_stats(full_weights, expected_returns, cov_matrix, returns_df, metadata_df, risk_free_rate)

    # If only 1 asset selected, set its weight to 1.0
    if k_selected == 1:
        full_weights[selected_indices[0]] = 1.0
        stats = compute_portfolio_stats(full_weights, expected_returns, cov_matrix, returns_df, metadata_df, risk_free_rate)
        stats["stage_b_success"] = True
        stats["status"] = "success"
        return stats

    # Extract sub-problem for selected assets
    mu_sub = expected_returns[selected_indices]
    cov_sub = cov_matrix[np.ix_(selected_indices, selected_indices)]

    # Initial equal weight guess
    w0 = np.ones(k_selected, dtype=float) / k_selected

    # Objective function: minimize - (w^T mu - lambda * w^T Sigma w)
    def objective(w):
        ret = np.dot(w, mu_sub)
        var = np.dot(w, np.dot(cov_sub, w))
        return - (ret - risk_aversion * var)

    def objective_jacobian(w):
        return - (mu_sub - 2.0 * risk_aversion * np.dot(cov_sub, w))

    # Constraints list
    constraints = []

    # 1. Fully invested constraint: sum(w) = 1.0
    constraints.append({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})

    # 2. Sector weight constraints if metadata available
    if metadata_df is not None and "Sector" in metadata_df.columns and max_sector_weight < 1.0:
        selected_sectors = metadata_df.iloc[selected_indices]["Sector"].tolist()
        unique_sectors = set(selected_sectors)

        for sec in unique_sectors:
            sec_mask = np.array([s == sec for s in selected_sectors], dtype=float)
            constraints.append({
                "type": "ineq",
                "fun": lambda w, mask=sec_mask: max_sector_weight - np.dot(w, mask)
            })

    # 3. Optional target return constraint: w^T mu >= target_return
    if target_return is not None:
        constraints.append({
            "type": "ineq",
            "fun": lambda w: np.dot(w, mu_sub) - target_return
        })

    # 4. Optional target volatility constraint: sqrt(w^T Sigma w) <= target_volatility
    if target_volatility is not None and target_volatility > 0:
        constraints.append({
            "type": "ineq",
            "fun": lambda w: target_volatility - np.sqrt(max(0.0, np.dot(w, np.dot(cov_sub, w))))
        })

    # Bounds on individual asset weights
    bounds = [(min_weight, max_weight) for _ in range(k_selected)]

    # Run SLSQP optimization
    res = minimize(
        fun=objective,
        x0=w0,
        method="SLSQP",
        jac=objective_jacobian,
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-8}
    )

    if res.success:
        w_opt = res.x
        sum_w = np.sum(w_opt)

        violations = []

        # Check raw weight sum before any adjustments
        if abs(sum_w - 1.0) > SUM_TOLERANCE:
            violations.append(f"Raw weight sum {sum_w:.8f} != 1.0 (exceeds sum tolerance {SUM_TOLERANCE})")
        else:
            w_opt = w_opt / sum_w  # Normalize tiny numerical drift

        if np.any(w_opt > max_weight + CONSTRAINT_TOLERANCE):
            violations.append(f"Max weight limit ({max_weight:.1%}) exceeded")

        if np.any(w_opt < min_weight - CONSTRAINT_TOLERANCE):
            violations.append(f"Min weight limit ({min_weight:.1%}) violated")

        if metadata_df is not None and "Sector" in metadata_df.columns and max_sector_weight < 1.0:
            selected_sectors = metadata_df.iloc[selected_indices]["Sector"].tolist()
            for sec in set(selected_sectors):
                sec_mask = np.array([s == sec for s in selected_sectors], dtype=float)
                sec_w = float(np.dot(w_opt, sec_mask))
                if sec_w > max_sector_weight + CONSTRAINT_TOLERANCE:
                    violations.append(f"Sector '{sec}' weight ({sec_w:.1%}) exceeds limit ({max_sector_weight:.1%})")

        if target_return is not None:
            ret_achieved = float(np.dot(w_opt, mu_sub))
            if ret_achieved < target_return - CONSTRAINT_TOLERANCE:
                violations.append(f"Target return ({target_return:.2%}) not met ({ret_achieved:.2%})")

        if target_volatility is not None and target_volatility > 0:
            vol_achieved = float(np.sqrt(max(0.0, np.dot(w_opt, np.dot(cov_sub, w_opt)))))
            if vol_achieved > target_volatility + CONSTRAINT_TOLERANCE:
                violations.append(f"Target volatility ({target_volatility:.2%}) exceeded ({vol_achieved:.2%})")

        if len(violations) > 0:
            full_weights[selected_indices] = 0.0
            stats = compute_portfolio_stats(
                weights=full_weights,
                expected_returns=expected_returns,
                cov_matrix=cov_matrix,
                returns_df=returns_df,
                metadata_df=metadata_df,
                risk_free_rate=risk_free_rate
            )
            stats["stage_b_success"] = False
            stats["status"] = "constraint_validation_failed"
            stats["stage_b_message"] = "Post-optimization constraint violations: " + " | ".join(violations)
            return stats

        full_weights[selected_indices] = w_opt
        stats = compute_portfolio_stats(
            weights=full_weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            returns_df=returns_df,
            metadata_df=metadata_df,
            risk_free_rate=risk_free_rate
        )
        stats["stage_b_success"] = True
        stats["status"] = "success"
        stats["stage_b_message"] = res.message
        return stats
    else:
        # SLSQP failed -> DO NOT fall back to equal weighting! Mark failed and zero weights.
        full_weights.fill(0.0)
        stats = compute_portfolio_stats(
            weights=full_weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            returns_df=returns_df,
            metadata_df=metadata_df,
            risk_free_rate=risk_free_rate
        )
        stats["stage_b_success"] = False
        stats["status"] = "optimization_failed"
        stats["stage_b_message"] = f"Stage-B SLSQP continuous optimization failed: {res.message}"
        return stats
