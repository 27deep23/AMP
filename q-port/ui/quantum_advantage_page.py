"""
Quantum Advantage & Scaling Explorer UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

from utils.caching import get_cached_preprocessed_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix
from core.classical_optimizer import solve_greedy, solve_simulated_annealing, solve_exact_enumeration
from core.quantum_optimizer import solve_qaoa


def render_quantum_advantage_page():
    st.title("🚀 Quantum Advantage & Scaling Explorer")
    st.caption("Empirical scalability analysis comparing QAOA quantum simulation vs classical solvers across problem dimensions N.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)

    st.markdown("""
    Evaluate how runtime (seconds) and QUBO objective quality scale as the number of candidate assets $N$ increases from 10 to 25.
    """)

    if st.button("🚀 Run Scaling Experiment (N = 10, 15, 20, 25)", type="primary", use_container_width=True):
        scaling_records = []
        dimensions = [10, 15, 20, 25]

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, n in enumerate(dimensions):
            status_text.text(f"Evaluating dimension N={n} assets...")
            
            sub_returns = returns_df.iloc[:, :n]
            sub_meta = clean_meta.iloc[:n]
            k_target = max(2, n // 3)

            mu = compute_expected_returns(sub_returns)
            cov = compute_covariance_matrix(sub_returns)
            Q, offset, _ = build_qubo_matrix(mu, cov, k_target, metadata_df=sub_meta)

            # 1. Greedy
            _, cost_g, t_g, _ = solve_greedy(Q, offset, k_target)
            scaling_records.append({"N": n, "Method": "Greedy", "Runtime (s)": t_g, "QUBO Cost": cost_g})

            # 2. Simulated Annealing
            _, cost_sa, t_sa, _ = solve_simulated_annealing(Q, offset, k_target, max_steps=2000)
            scaling_records.append({"N": n, "Method": "Simulated Annealing", "Runtime (s)": t_sa, "QUBO Cost": cost_sa})

            # 3. Exact (only if N <= 20)
            if n <= 20:
                try:
                    _, cost_ex, t_ex, _ = solve_exact_enumeration(Q, offset, k_target, max_runtime_sec=5.0)
                    scaling_records.append({"N": n, "Method": "Exact Enumeration", "Runtime (s)": t_ex, "QUBO Cost": cost_ex})
                except Exception:
                    pass

            # 4. QAOA (only if N <= 20 to prevent local CPU simulator memory overflow)
            if n <= 20:
                _, cost_q, t_q, _ = solve_qaoa(Q, offset, k_target, shots=256, max_runtime_sec=10.0)
                scaling_records.append({"N": n, "Method": "QAOA (Quantum Aer)", "Runtime (s)": t_q, "QUBO Cost": cost_q})
            else:
                # Honest skip notification at N=25
                st.warning(f"⚠️ **N={n} Qubit Ceiling Exceeded**: QAOA quantum simulation skipped above 24 qubits to prevent local CPU memory overflow.")

            progress_bar.progress((idx + 1) / len(dimensions))

        status_text.text("Scaling experiment completed!")
        df_scaling = pd.DataFrame(scaling_records)
        st.session_state["scaling_df"] = df_scaling

    if "scaling_df" in st.session_state:
        df_scaling = st.session_state["scaling_df"]

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            fig_time = px.line(
                df_scaling,
                x="N",
                y="Runtime (s)",
                color="Method",
                markers=True,
                log_y=True,
                title="Runtime Scaling vs Dimension N (Log Scale)"
            )
            fig_time.update_layout(height=420)
            st.plotly_chart(fig_time, use_container_width=True)

        with c2:
            fig_cost = px.line(
                df_scaling,
                x="N",
                y="QUBO Cost",
                color="Method",
                markers=True,
                title="QUBO Objective Quality vs Dimension N"
            )
            fig_cost.update_layout(height=420)
            st.plotly_chart(fig_cost, use_container_width=True)

        st.dataframe(df_scaling, use_container_width=True)
