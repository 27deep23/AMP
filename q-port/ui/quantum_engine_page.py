"""
QAOA Quantum Simulator & Circuit Inspector UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix
from core.quantum_optimizer import solve_qaoa, qubo_to_ising, build_qaoa_circuit


def render_quantum_engine_page():
    st.title("⚛️ QAOA Quantum Engine & Circuit Inspector")
    st.caption("Local CPU Quantum Simulation powered by Qiskit Aer (AerSimulator).")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Quantum Execution Controls")
        n_qubits = st.slider("Qubit Count (N)", min_value=2, max_value=20, value=6, step=1)
        k_target = st.slider("Target Cardinality (K)", min_value=1, max_value=n_qubits, value=min(3, n_qubits))
        p_layers = st.selectbox("QAOA Layers (p)", [1, 2], index=0)
        shots = st.select_slider("Measurement Shots", options=[256, 512, 1024, 2048], value=1024)
        seed = st.number_input("Simulator Random Seed", value=42)

        run_btn = st.button("🚀 Execute QAOA Simulation", type="primary", use_container_width=True)

    mu = compute_expected_returns(returns_df.iloc[:, :n_qubits])
    cov = compute_covariance_matrix(returns_df.iloc[:, :n_qubits])
    meta = clean_meta.iloc[:n_qubits]

    Q, offset, qubo_info = build_qubo_matrix(mu, cov, k_target, metadata_df=meta)
    h, J, ising_offset = qubo_to_ising(Q, offset)

    with col2:
        st.subheader("Circuit Architecture Metrics")
        # Build 1 circuit for metric inspection
        sample_qc = build_qaoa_circuit(n_qubits, h, J, 0.5, 0.5)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Qubits", sample_qc.num_qubits)
        m2.metric("Circuit Depth", sample_qc.depth())
        m3.metric("Total Gates", sum(sample_qc.count_ops().values()))
        m4.metric("Hardware Target", "Qiskit Aer CPU")

        st.markdown("#### Gate Breakdown")
        st.json(dict(sample_qc.count_ops()))

    st.divider()

    if run_btn:
        with st.spinner(f"Running QAOA simulation for N={n_qubits} qubits on local Aer CPU..."):
            best_x, best_cost, runtime, metrics = solve_qaoa(
                Q=Q,
                offset=offset,
                k_target=k_target,
                p=p_layers,
                shots=shots,
                seed=seed
            )

            st.success(f"✅ QAOA Simulation completed in {runtime:.3f} seconds!")

            res_m1, res_m2, res_m3, res_m4 = st.columns(4)
            res_m1.metric("Optimal QUBO Cost", f"{best_cost:.4f}")
            res_m2.metric("Feasible Sampling Rate", f"{metrics['feasible_rate'] * 100.0:.1f}%")
            res_m3.metric("Optimal State Prob.", f"{metrics['best_probability'] * 100.0:.1f}%")
            res_m4.metric("Optimal Bitstring", "".join(str(b) for b in best_x))

            # Display selected assets
            selected_tickers = list(meta["Ticker"].iloc[np.where(best_x == 1)[0]])
            st.markdown(f"**Selected Asset Subset**: `{', '.join(selected_tickers)}`")

    else:
        st.info("Click **Execute QAOA Simulation** above to run the Qiskit Aer simulation.")
