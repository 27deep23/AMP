"""
Unit tests for Q-PORT Benchmark Engine (core/benchmark.py).
"""

import pytest
import numpy as np
import pandas as pd
from core.data_loader import fetch_market_data
from core.preprocessing import preprocess_data
from core.benchmark import run_benchmark_suite


def test_benchmark_suite_execution():
    """Verify benchmark engine runs all algorithms on bundled dataset and produces valid results table."""
    prices_df, meta_df, _ = fetch_market_data(force_bundled=True)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)
    
    # Subset to 10 assets for fast testing
    returns_df = returns_df.iloc[:, :10]
    clean_meta = clean_meta.iloc[:10]

    results_df, bench_info = run_benchmark_suite(
        returns_df=returns_df,
        metadata_df=clean_meta,
        k_target=3,
        run_qaoa=True,
        run_exact=True,
        qaoa_p=1,
        qaoa_shots=256,
        seed=42
    )

    assert not results_df.empty
    methods = results_df["Method"].tolist()
    assert "Greedy" in methods
    assert "Simulated Annealing" in methods
    assert "Exact Enumeration" in methods
    assert "QAOA (Quantum)" in methods
    assert "Equal Weight (1/N)" in methods
    assert "Continuous Mean-Variance" in methods

    assert bench_info["is_exact_reference"] is True
    assert bench_info["reference_baseline_name"] == "Exact Enumeration (Global Optimum)"

    # Exact Enumeration gap must be 0.0%
    exact_row = results_df[results_df["Method"] == "Exact Enumeration"]
    assert pytest.approx(exact_row["Optimality Gap (%)"].values[0], abs=1e-5) == 0.0
