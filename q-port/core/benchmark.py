"""
Benchmark Engine for Q-PORT.
Fairly evaluates and compares Quantum (QAOA) against Classical solvers (Greedy, SA, Exact, Equal Weight, Continuous MV)
under identical financial data, QUBO formulation, and Stage-B continuous allocation rules.
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from core.qubo import build_qubo_matrix, evaluate_qubo_cost
from core.classical_optimizer import solve_greedy, solve_simulated_annealing, solve_exact_enumeration
from core.quantum_optimizer import solve_qaoa
from core.portfolio import optimize_continuous_weights
from core.statistics import compute_portfolio_stats


from config.settings import DEFAULT_QAOA_P, DEFAULT_SHOTS


def run_benchmark_suite(
    returns_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    k_target: int,
    risk_aversion: float = 1.0,
    max_weight: float = 1.0,
    max_sector_weight: float = 1.0,
    target_return: Optional[float] = None,
    target_volatility: Optional[float] = None,
    run_qaoa: bool = True,
    run_exact: bool = True,
    qaoa_p: int = DEFAULT_QAOA_P,
    qaoa_shots: int = DEFAULT_SHOTS,
    risk_free_rate: float = 0.06,
    seed: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Runs comprehensive benchmark comparing QAOA, Greedy, SA, Exact, Equal Weight, and Continuous MV.
    
    Returns:
        results_df: Comparative DataFrame across all evaluated algorithms
        benchmark_info: Metadata detailing benchmark execution, baseline reference type, and timing
    """
    from core.statistics import compute_expected_returns, compute_covariance_matrix

    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)
    n = len(mu)

    # Build QUBO matrix
    Q, offset, qubo_info = build_qubo_matrix(
        expected_returns=mu,
        cov_matrix=cov,
        k_target=k_target,
        risk_aversion=risk_aversion,
        metadata_df=metadata_df
    )

    results_list = []
    solver_data = {}

    # 1. Greedy Heuristic
    x_greedy, cost_greedy, t_greedy, m_greedy = solve_greedy(Q, offset, k_target)
    stats_greedy = optimize_continuous_weights(
        x_greedy, mu, cov, risk_aversion, max_weight, 0.0, max_sector_weight,
        target_return, target_volatility, returns_df, metadata_df, risk_free_rate
    )
    solver_data["Greedy"] = {"x": x_greedy, "qubo_cost": cost_greedy, "runtime": t_greedy, "stats": stats_greedy}

    # 2. Simulated Annealing
    x_sa, cost_sa, t_sa, m_sa = solve_simulated_annealing(Q, offset, k_target, seed=seed)
    stats_sa = optimize_continuous_weights(
        x_sa, mu, cov, risk_aversion, max_weight, 0.0, max_sector_weight,
        target_return, target_volatility, returns_df, metadata_df, risk_free_rate
    )
    solver_data["Simulated Annealing"] = {"x": x_sa, "qubo_cost": cost_sa, "runtime": t_sa, "stats": stats_sa}

    # 3. Exact Enumeration (if requested and N <= 22)
    x_exact, cost_exact, t_exact = None, None, None
    m_exact = {}
    has_exact = False
    if run_exact and n <= 22:
        try:
            x_exact, cost_exact, t_exact, m_exact = solve_exact_enumeration(Q, offset, k_target)
            if x_exact is not None and m_exact.get("is_exact", False):
                stats_exact = optimize_continuous_weights(
                    x_exact, mu, cov, risk_aversion, max_weight, 0.0, max_sector_weight,
                    target_return, target_volatility, returns_df, metadata_df, risk_free_rate
                )
                solver_data["Exact Enumeration"] = {
                    "x": x_exact,
                    "qubo_cost": cost_exact,
                    "runtime": t_exact,
                    "stats": stats_exact,
                    "is_exact": True
                }
                has_exact = True
            else:
                has_exact = False
        except Exception:
            has_exact = False

    # 4. QAOA Quantum Engine (if requested and N <= 24)
    if run_qaoa and n <= 24:
        x_qaoa, cost_qaoa, t_qaoa, m_qaoa = solve_qaoa(Q, offset, k_target, p=qaoa_p, shots=qaoa_shots, seed=seed)
        if x_qaoa is not None:
            stats_qaoa = optimize_continuous_weights(
                x_qaoa, mu, cov, risk_aversion, max_weight, 0.0, max_sector_weight,
                target_return, target_volatility, returns_df, metadata_df, risk_free_rate
            )
            solver_data["QAOA (Quantum)"] = {"x": x_qaoa, "qubo_cost": cost_qaoa, "runtime": t_qaoa, "stats": stats_qaoa, "quantum_metrics": m_qaoa}

    # 5. Equal Weight Baseline (1/N across all N assets)
    t0_eq = time.perf_counter()
    x_eq = np.ones(n, dtype=int)
    w_eq = np.ones(n, dtype=float) / n
    stats_eq = compute_portfolio_stats(w_eq, mu, cov, returns_df, metadata_df, risk_free_rate)
    cost_eq = evaluate_qubo_cost(x_eq, Q, offset)
    t_eq = time.perf_counter() - t0_eq
    solver_data["Equal Weight (1/N)"] = {"x": x_eq, "qubo_cost": cost_eq, "runtime": t_eq, "stats": stats_eq}

    # 6. Unconstrained Classical Continuous Mean-Variance Baseline
    t0_mv = time.perf_counter()
    x_unconstrained = np.ones(n, dtype=int)
    stats_mv = optimize_continuous_weights(
        x_unconstrained, mu, cov, risk_aversion, max_weight, 0.0, max_sector_weight,
        target_return, target_volatility, returns_df, metadata_df, risk_free_rate
    )
    cost_mv = evaluate_qubo_cost(x_unconstrained, Q, offset)
    t_mv = time.perf_counter() - t0_mv
    solver_data["Continuous Mean-Variance"] = {"x": x_unconstrained, "qubo_cost": cost_mv, "runtime": t_mv, "stats": stats_mv}

    # Determine baseline reference cost & terminology for Optimality Gap calculation
    if has_exact and cost_exact is not None:
        ref_cost = cost_exact
        ref_name = "Exact Optimum"
        gap_col_name = "Optimality Gap (%)"
    elif m_exact.get("timed_out", False):
        ref_cost = min([data["qubo_cost"] for name, data in solver_data.items() if name in ["Greedy", "Simulated Annealing"]])
        ref_name = "Exact reference unavailable — runtime budget exceeded."
        gap_col_name = "Gap to Best Known Discrete Solution (%)"
    elif m_exact.get("budget_exceeded_states", False):
        ref_cost = min([data["qubo_cost"] for name, data in solver_data.items() if name in ["Greedy", "Simulated Annealing"]])
        ref_name = "Exact reference unavailable — state-count budget exceeded."
        gap_col_name = "Gap to Best Known Discrete Solution (%)"
    else:
        discrete_costs = [data["qubo_cost"] for name, data in solver_data.items() if name in ["Greedy", "Simulated Annealing"]]
        ref_cost = min(discrete_costs) if discrete_costs else cost_greedy
        ref_name = "Best Known Discrete Solution (Classical Heuristic)"
        gap_col_name = "Gap to Best Known Discrete Solution (%)"

    # Assemble summary table
    tickers = list(returns_df.columns)
    for method_name, data in solver_data.items():
        st = data["stats"]
        cost = data["qubo_cost"]
        x_vec = data["x"]
        selected_tickers = [tickers[idx] for idx, val in enumerate(x_vec) if val == 1]

        # Calculate Gap (%)
        if ref_cost != 0 and cost is not None:
            gap_pct = float((cost - ref_cost) / abs(ref_cost) * 100.0)
        else:
            gap_pct = 0.0

        is_feasible = (int(np.sum(x_vec)) == k_target) if method_name not in ["Equal Weight (1/N)", "Continuous Mean-Variance"] else True

        results_list.append({
            "Method": method_name,
            "Stage-A QUBO Cost": cost,
            "Optimality Gap (%)": gap_pct if has_exact else None,
            "Gap to Best Known Discrete Solution (%)": gap_pct,
            "Expected Return (%)": st["expected_return"] * 100.0,
            "Annual Volatility (%)": st["volatility"] * 100.0,
            "Sharpe Ratio": st["sharpe_ratio"],
            "Max Drawdown (%)": st["max_drawdown"] * 100.0,
            "HHI Index": st["hhi"],
            "Active Assets": st["active_asset_count"],
            "Feasible": is_feasible,
            "Runtime (s)": data["runtime"],
            "Selected Assets": ", ".join(selected_tickers) if len(selected_tickers) <= 8 else f"{len(selected_tickers)} assets"
        })

    results_df = pd.DataFrame(results_list)

    benchmark_info = {
        "reference_baseline_name": ref_name,
        "reference_cost": ref_cost,
        "is_exact_reference": has_exact,
        "optimality_certified": has_exact,
        "gap_column_name": gap_col_name,
        "n_assets": n,
        "k_target": k_target,
        "risk_aversion": risk_aversion,
        "qaoa_p": qaoa_p,
        "qaoa_shots": qaoa_shots,
        "seed": seed
    }

    return results_df, benchmark_info
