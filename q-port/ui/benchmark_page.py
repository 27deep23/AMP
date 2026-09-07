"""
Quantum vs Classical Head-to-Head Benchmark UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data
from utils.formatting import format_sec
from core.benchmark import run_benchmark_suite


def render_benchmark_page():
    st.title("🏆 Quantum vs Classical Head-to-Head Benchmark")
    st.caption("Fair comparative evaluation across QAOA, Greedy, SA, Exact Enumeration, Equal Weight, and Continuous MV.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)
    total_assets = len(clean_prices.columns)

    st.sidebar.markdown("### 🎛️ Benchmark Settings")
    n_assets = st.sidebar.slider("Asset Universe Size (N)", min_value=4, max_value=total_assets, value=15)
    k_target = st.sidebar.slider("Target Portfolio Size (K)", min_value=1, max_value=n_assets, value=5)

    risk_aversion = st.sidebar.slider("Risk Aversion (λ)", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
    max_weight = st.sidebar.slider("Max Asset Weight (w_max)", min_value=0.10, max_value=1.0, value=0.35, step=0.05)
    max_sector_weight = st.sidebar.slider("Max Sector Weight", min_value=0.20, max_value=1.0, value=0.50, step=0.05)

    run_exact = st.sidebar.checkbox("Include Exact Solver (if N <= 22)", value=True)
    run_qaoa = st.sidebar.checkbox("Include QAOA Quantum Engine", value=True)

    if st.button("🚀 Run Head-to-Head Benchmark Suite", type="primary", use_container_width=True):
        sub_returns = returns_df.iloc[:, :n_assets]
        sub_meta = clean_meta.iloc[:n_assets]

        with st.spinner("Executing benchmark across all combinatorial and continuous solvers..."):
            results_df, bench_info = run_benchmark_suite(
                returns_df=sub_returns,
                metadata_df=sub_meta,
                k_target=k_target,
                risk_aversion=risk_aversion,
                max_weight=max_weight,
                max_sector_weight=max_sector_weight,
                run_qaoa=run_qaoa,
                run_exact=run_exact,
                seed=42
            )

            st.session_state["benchmark_results"] = results_df
            st.session_state["benchmark_info"] = bench_info

    if "benchmark_results" in st.session_state:
        results_df = st.session_state["benchmark_results"]
        bench_info = st.session_state["benchmark_info"]

        st.subheader(f"Benchmark Results (N={bench_info['n_assets']}, K={bench_info['k_target']})")
        st.caption(f"Reference Baseline Type: **{bench_info['reference_baseline_name']}**")

        st.dataframe(results_df, use_container_width=True)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            fig_sharpe = px.bar(
                results_df,
                x="Method",
                y="Sharpe Ratio",
                color="Method",
                title="Sharpe Ratio Comparison",
                text_auto=".2f"
            )
            fig_sharpe.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_sharpe, use_container_width=True)

        with c2:
            fig_gap = px.bar(
                results_df,
                x="Method",
                y="Optimality Gap (%)",
                color="Method",
                title=f"Optimality Gap (%) vs {bench_info['reference_baseline_name']}",
                text_auto=".2f"
            )
            fig_gap.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_gap, use_container_width=True)

    else:
        st.info("Click **Run Head-to-Head Benchmark Suite** above to initiate execution.")
