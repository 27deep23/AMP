"""
Executive Dashboard UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.caching import get_cached_preprocessed_data
from utils.formatting import format_inr, format_pct, format_sec
from core.benchmark import run_benchmark_suite
from core.explainability import generate_portfolio_explainability


def render_dashboard_page():
    st.title("🏛️ Executive Dashboard — Q-PORT")
    st.caption("Quantum Portfolio Intelligence & Optimisation Platform · UC-018 Asset Manager Portfolio Optimisation")

    st.markdown("""
    Welcome to **Q-PORT**, a hybrid quantum-classical portfolio optimization platform designed for asset managers.
    Q-PORT formulates constrained discrete asset selection as a **QUBO** (Quadratic Unconstrained Binary Optimization) problem, 
    solves it via **QAOA** on local quantum simulation, and optimizes continuous allocations via **SciPy SLSQP**.
    """)

    st.divider()

    # Judge Mode Banner
    col_demo, col_info = st.columns([1, 2])
    with col_demo:
        st.subheader("⚡ Judge Mode / Demo")
        if st.button("🚀 RUN 3-MINUTE DEMO", type="primary", use_container_width=True):
            with st.spinner("Running full 15-asset benchmark suite (QAOA, Greedy, SA, Exact, SLSQP)..."):
                clean_prices, returns_df, clean_meta, quality_report, _ = get_cached_preprocessed_data(force_bundled=True)
                
                # Subset to 15 assets
                returns_15 = returns_df.iloc[:, :15]
                meta_15 = clean_meta.iloc[:15]

                results_df, bench_info = run_benchmark_suite(
                    returns_df=returns_15,
                    metadata_df=meta_15,
                    k_target=5,
                    run_qaoa=True,
                    run_exact=True,
                    qaoa_p=1,
                    qaoa_shots=512,
                    seed=42
                )
                st.session_state["benchmark_results"] = results_df
                st.session_state["benchmark_info"] = bench_info
                st.session_state["demo_run_complete"] = True
                st.success("✅ Demo benchmark execution complete!")

    with col_info:
        st.info("""
        **Quick Demo Setup**:
        - Asset Universe: 15 Indian Large-Cap Equities (NSE/BSE)
        - Target Selection: $K = 5$ assets
        - Capital Investment: ₹10,00,000
        - Solvers: QAOA (Qiskit Aer), Greedy, Simulated Annealing, Exact Enumeration
        """)

    st.divider()

    # Display results if available
    if "benchmark_results" in st.session_state:
        results_df = st.session_state["benchmark_results"]
        bench_info = st.session_state["benchmark_info"]

        st.subheader("📊 Latest Benchmark Performance Overview")

        # Key Metrics Row
        qaoa_row = results_df[results_df["Method"] == "QAOA (Quantum)"]
        exact_row = results_df[results_df["Method"] == "Exact Enumeration"]
        greedy_row = results_df[results_df["Method"] == "Greedy"]

        m1, m2, m3, m4, m5 = st.columns(5)
        if not qaoa_row.empty:
            m1.metric("QAOA Expected Return", f"{qaoa_row['Expected Return (%)'].values[0]:.2f}%")
            m2.metric("QAOA Volatility", f"{qaoa_row['Annual Volatility (%)'].values[0]:.2f}%")
            m3.metric("QAOA Sharpe Ratio", f"{qaoa_row['Sharpe Ratio'].values[0]:.2f}")
            m4.metric("QAOA Optimality Gap", f"{qaoa_row['Optimality Gap (%)'].values[0]:.2f}%")
            m5.metric("QAOA Runtime", format_sec(qaoa_row['Runtime (s)'].values[0]))

        st.divider()

        # Comparative Visualizations
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("#### Sharpe Ratio Comparison")
            fig_sharpe = px.bar(
                results_df,
                x="Method",
                y="Sharpe Ratio",
                color="Method",
                title="Sharpe Ratio across Solvers",
                text_auto=".2f"
            )
            fig_sharpe.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig_sharpe, use_container_width=True)

        with col_c2:
            st.markdown("#### Optimality Gap (%) vs Baseline")
            fig_gap = px.bar(
                results_df,
                x="Method",
                y="Optimality Gap (%)",
                color="Method",
                title=f"Optimality Gap vs {bench_info.get('reference_baseline_name', 'Baseline')}",
                text_auto=".2f"
            )
            fig_gap.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig_gap, use_container_width=True)

        st.markdown("#### Benchmark Results Summary Table")
        st.dataframe(results_df, use_container_width=True)

    else:
        st.warning("⚠️ No benchmark run stored in memory yet. Click **RUN 3-MINUTE DEMO** above or navigate to the **Benchmark** page.")
