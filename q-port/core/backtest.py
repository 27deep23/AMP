"""
Walk-Forward Backtesting Engine for Q-PORT.
Strictly eliminates look-ahead bias by optimizing portfolio weights on historical in-sample training windows
and evaluating performance on unseen out-of-sample test windows.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

from core.preprocessing import preprocess_data
from core.statistics import compute_expected_returns, compute_covariance_matrix, compute_max_drawdown, compute_portfolio_stats
from core.qubo import build_qubo_matrix
from core.classical_optimizer import solve_greedy, solve_simulated_annealing
from core.portfolio import optimize_continuous_weights


def run_walk_forward_backtest(
    prices_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    k_target: int,
    train_window_days: int = 252,
    test_window_days: int = 63,
    risk_aversion: float = 1.0,
    max_weight: float = 1.0,
    max_sector_weight: float = 1.0,
    risk_free_rate: float = 0.06,
    seed: int = 42,
    run_qaoa_in_backtest: bool = False,
    qaoa_p: int = 1,
    qaoa_shots: int = 512
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executes walk-forward backtest.
    
    Returns:
        equity_curves_df: Daily cumulative out-of-sample return series for each strategy
        summary_metrics_df: Table of out-of-sample performance metrics (CAGR, Vol, Sharpe, MaxDD)
        backtest_info: Execution metadata including rebalance dates and window parameters
    """
    from core.quantum_optimizer import solve_qaoa

    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, metadata_df)
    n_days = len(returns_df)

    if n_days < train_window_days + test_window_days:
        raise ValueError(
            f"Insufficient historical data ({n_days} days) for train window ({train_window_days}) "
            f"and test window ({test_window_days}). Total needed: {train_window_days + test_window_days}."
        )

    dates = returns_df.index
    n_assets = returns_df.shape[1]

    use_real_qaoa = run_qaoa_in_backtest and (n_assets <= 24)
    qport_label = "Q-PORT (Hybrid QAOA)"

    strategies = [qport_label, "Equal Weight (1/N)", "Continuous Mean-Variance", "Greedy Heuristic"]

    # Storage for out-of-sample daily returns
    oos_returns = {strat: [] for strat in strategies}
    oos_dates = []

    # Rebalance step indices
    rebal_starts = list(range(train_window_days, n_days, test_window_days))

    for start_idx in rebal_starts:
        train_start = start_idx - train_window_days
        train_end = start_idx
        test_end = min(start_idx + test_window_days, n_days)

        train_rets = returns_df.iloc[train_start:train_end]
        test_rets = returns_df.iloc[train_end:test_end]

        if test_rets.empty:
            break

        # Compute train statistics (NO look-ahead)
        mu_train = compute_expected_returns(train_rets)
        cov_train = compute_covariance_matrix(train_rets)

        # Build QUBO on train data
        Q, offset, _ = build_qubo_matrix(mu_train, cov_train, k_target, risk_aversion, metadata_df=clean_meta)

        # Greedy Heuristic weights
        x_greedy, _, _, _ = solve_greedy(Q, offset, k_target)
        st_greedy = optimize_continuous_weights(x_greedy, mu_train, cov_train, risk_aversion, max_weight, 0.0, max_sector_weight, metadata_df=clean_meta)
        w_greedy = st_greedy["weights"]

        # Q-PORT weights calculation
        qaoa_status = "not_executed"
        qaoa_runtime = 0.0
        qaoa_feasible = False

        if use_real_qaoa:
            try:
                x_qaoa, cost_qaoa, t_qaoa, m_qaoa = solve_qaoa(Q, offset, k_target, p=qaoa_p, shots=qaoa_shots, seed=seed)
                qaoa_status = m_qaoa.get("status", "unknown")
                qaoa_runtime = t_qaoa
                qaoa_feasible = m_qaoa.get("is_feasible", False)

                if x_qaoa is not None and qaoa_status == "success":
                    st_qaoa = optimize_continuous_weights(x_qaoa, mu_train, cov_train, risk_aversion, max_weight, 0.0, max_sector_weight, metadata_df=clean_meta)
                    if st_qaoa.get("stage_b_success", False):
                        w_qport = st_qaoa["weights"]
                    else:
                        w_qport = np.zeros(len(mu_train))
                else:
                    # Period unavailable - zero return, do not silently substitute Greedy/Equal Weight!
                    w_qport = np.zeros(len(mu_train))
            except Exception:
                qaoa_status = "failed"
                qaoa_feasible = False
                w_qport = np.zeros(len(mu_train))
        else:
            # QAOA not executed in backtest config - mark period unavailable with zero return, NEVER substitute Greedy
            w_qport = np.zeros(len(mu_train))

        # Equal Weight 1/N
        w_eq = np.ones(len(mu_train), dtype=float) / len(mu_train)

        # Continuous Mean-Variance
        x_all = np.ones(len(mu_train), dtype=int)
        st_mv = optimize_continuous_weights(x_all, mu_train, cov_train, risk_aversion, max_weight, 0.0, max_sector_weight, metadata_df=clean_meta)
        w_mv = st_mv["weights"]

        # Evaluate on test window
        test_rets_arr = test_rets.to_numpy()
        
        r_qport = np.dot(test_rets_arr, w_qport)
        r_eq = np.dot(test_rets_arr, w_eq)
        r_mv = np.dot(test_rets_arr, w_mv)
        r_greedy = np.dot(test_rets_arr, w_greedy)

        oos_returns[qport_label].extend(r_qport)
        oos_returns["Equal Weight (1/N)"].extend(r_eq)
        oos_returns["Continuous Mean-Variance"].extend(r_mv)
        oos_returns["Greedy Heuristic"].extend(r_greedy)
        oos_dates.extend(test_rets.index)

    # Build out-of-sample equity curves
    equity_curves = {"Date": oos_dates}
    metrics_records = []

    for strat in strategies:
        r_arr = np.array(oos_returns[strat])
        max_dd, cum_series, cagr = compute_max_drawdown(r_arr)
        
        annual_vol = float(np.std(r_arr) * np.sqrt(252.0))
        annual_ret = float(np.mean(r_arr) * 252.0)
        sharpe = float((annual_ret - risk_free_rate) / annual_vol) if annual_vol > 1e-8 else 0.0

        equity_curves[strat] = cum_series

        metrics_records.append({
            "Strategy": strat,
            "CAGR (%)": cagr * 100.0,
            "Annualized Return (%)": annual_ret * 100.0,
            "Annualized Volatility (%)": annual_vol * 100.0,
            "Sharpe Ratio": sharpe,
            "Max Drawdown (%)": max_dd * 100.0,
            "Win Rate (%)": float(np.sum(r_arr > 0) / len(r_arr) * 100.0) if len(r_arr) > 0 else 0.0
        })

    equity_curves_df = pd.DataFrame(equity_curves).set_index("Date")
    summary_metrics_df = pd.DataFrame(metrics_records)

    backtest_info = {
        "train_window_days": train_window_days,
        "test_window_days": test_window_days,
        "total_rebalance_cycles": len(rebal_starts),
        "total_oos_days": len(oos_dates),
        "start_date": str(oos_dates[0].date()) if oos_dates else "",
        "end_date": str(oos_dates[-1].date()) if oos_dates else "",
        "qaoa_real_execution": use_real_qaoa,
        "qport_label": qport_label,
        "periods_evaluated": len(rebal_starts),
        "successful_qaoa_periods": len(rebal_starts) if not use_real_qaoa else sum(1 for _ in rebal_starts if qaoa_status == "success"),
        "failed_periods": 0 if not use_real_qaoa else sum(1 for _ in rebal_starts if qaoa_status in ["failed", "optimization_failed"]),
        "timeout_periods": 0 if not use_real_qaoa else sum(1 for _ in rebal_starts if qaoa_status == "timeout"),
        "unavailable_periods": 0 if not use_real_qaoa else sum(1 for _ in rebal_starts if qaoa_status in ["no_feasible_solution", "timeout", "failed"])
    }

    return equity_curves_df, summary_metrics_df, backtest_info
