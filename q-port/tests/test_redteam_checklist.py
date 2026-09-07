"""
Red-Team Test Suite: Final 10/10 Verification Checklist.
Covers manual penalty overrides, timeout enforcement, shot consistency, parameter propagation,
Stage-B failure isolation, covariance epsilon propagation, and reproducibility JSON schema.
"""

import pytest
import numpy as np
import pandas as pd
from config.settings import QPortConfig, COVARIANCE_EPSILON
from core.qubo import build_qubo_matrix, calibrate_penalties
from core.quantum_optimizer import solve_qaoa
from core.portfolio import optimize_continuous_weights
from core.statistics import compute_covariance_matrix
from core.classical_optimizer import solve_exact_enumeration
from core.benchmark import run_benchmark_suite
from core.backtest import run_walk_forward_backtest
from core.data_loader import fetch_market_data
from core.preprocessing import preprocess_data


def test_manual_penalty_override():
    """Verify manual A and B penalty overrides in QUBO construction."""
    mu = np.array([0.10, 0.20])
    cov = np.diag([0.04, 0.05])
    
    Q, offset, info = build_qubo_matrix(
        expected_returns=mu,
        cov_matrix=cov,
        k_target=1,
        manual_penalty_A=50.0,
        manual_penalty_B=50.0
    )
    assert info["penalty_A"] == 50.0
    assert info["penalty_B"] == 50.0
    assert info["is_manual_override"] is True


def test_qaoa_timeout():
    """Verify tiny max_runtime_sec triggers status='timeout' and returns None for best_x."""
    Q = np.diag([1.0, 2.0, 3.0, 4.0])
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=0.0,
        k_target=2,
        max_runtime_sec=0.0001
    )
    assert metrics["status"] == "timeout"
    assert best_x is None
    assert best_cost is None


def test_shot_count_consistency():
    """Verify optimization_shots and final_measurement_shots match the requested shot count."""
    Q = np.diag([1.0, 2.0])
    requested_shots = 2048
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=0.0,
        k_target=1,
        shots=requested_shots
    )
    assert metrics["optimization_shots"] == requested_shots
    assert metrics["final_measurement_shots"] == requested_shots
    assert metrics["shots"] == requested_shots


def test_max_iteration_propagation():
    """Verify configured max_iterations is recorded in metrics."""
    Q = np.diag([1.0, 2.0])
    best_x, best_cost, runtime, metrics = solve_qaoa(
        Q=Q,
        offset=0.0,
        k_target=1,
        max_iterations=150
    )
    assert metrics["configured_max_iterations"] == 150


def test_optimizer_selection():
    """Verify solver supports different optimizer selections (COBYLA, SPSA)."""
    Q = np.diag([1.0, 2.0])
    _, _, _, metrics_cobyla = solve_qaoa(Q, 0.0, 1, optimizer_name="COBYLA")
    _, _, _, metrics_spsa = solve_qaoa(Q, 0.0, 1, optimizer_name="SPSA")
    assert metrics_cobyla["optimizer_name"] == "COBYLA"
    assert metrics_spsa["optimizer_name"] == "SPSA"


def test_covariance_epsilon_propagation():
    """Verify compute_covariance_matrix uses COVARIANCE_EPSILON (1e-4)."""
    df = pd.DataFrame({"A": [0.01, 0.02, -0.01], "B": [0.02, -0.01, 0.01]})
    cov_reg = compute_covariance_matrix(df)
    cov_raw = df.cov().to_numpy() * 252
    diff = np.diag(cov_reg - cov_raw)
    np.testing.assert_array_almost_equal(diff, np.full(2, COVARIANCE_EPSILON))


def test_stage_b_failure():
    """Verify Stage-B optimization sets status='optimization_failed' and zero weights if SLSQP fails."""
    # Impossible constraints: min_weight 0.60 across 2 assets (sum > 1.0)
    mu = np.array([0.10, 0.20])
    cov = np.diag([0.04, 0.05])
    st = optimize_continuous_weights(
        selection_vector=np.array([1, 1]),
        expected_returns=mu,
        cov_matrix=cov,
        min_weight=0.60,
        max_weight=0.80
    )
    assert st["stage_b_success"] is False
    assert st["status"] in ["optimization_failed", "constraint_validation_failed"]
    assert np.all(st["weights"] == 0.0)


def test_reproducibility_export_keys():
    """Verify all required reproducibility keys are present in QPortConfig.to_dict()."""
    config = QPortConfig()
    export = config.to_dict()

    required_keys = [
        "seed", "data_source", "data_period", "asset_universe", "K", "K_min", "K_max",
        "lambda", "covariance_epsilon", "penalty_multiplier", "qaoa_p", "qaoa_parameter_count",
        "qaoa_optimizer", "configured_max_iterations", "optimization_shots", "final_measurement_shots",
        "exact_max_states", "exact_max_runtime_seconds", "active_qubit_ceiling"
    ]
    for key in required_keys:
        assert key in export, f"Missing reproducibility key '{key}' in QPortConfig export."


def test_exact_timeout():
    """Verify solve_exact_enumeration handles runtime timeout gracefully."""
    Q = np.zeros((16, 16))
    best_x, best_cost, runtime, metrics = solve_exact_enumeration(Q, 0.0, k_target=8, max_runtime_sec=0.0001)
    assert metrics["timed_out"] is True
    assert metrics["is_exact"] is False


def test_exact_result_terminology():
    """Verify exact result terminology logic under completed vs timed-out exact solver."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)

    sub_rets = returns_df.iloc[:, :6]
    sub_meta = clean_meta.iloc[:6]

    res_df, bench_info = run_benchmark_suite(sub_rets, sub_meta, k_target=3, run_exact=True)
    assert bench_info["is_exact_reference"] is True
    assert bench_info["reference_baseline_name"] == "Exact Optimum"
    assert bench_info["gap_column_name"] == "Optimality Gap (%)"
