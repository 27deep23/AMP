"""
Simulated Noise Sensitivity & Hardware Limits UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix
from core.noise_experiment import run_noise_sensitivity_experiment


def render_noise_page():
    st.title("🎛️ Simulated Noise Sensitivity & Hardware Limits")
    st.caption("Evaluate quantum algorithm degradation under simulated physical gate errors and decoherence.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Depolarizing Noise Parameters")
        p1 = st.slider("Single-Qubit Gate Error Rate (p1)", min_value=0.000, max_value=0.050, value=0.010, step=0.005, format="%.3f")
        p2 = st.slider("Two-Qubit Gate Error Rate (p2)", min_value=0.000, max_value=0.100, value=0.030, step=0.005, format="%.3f")
        n_qubits = st.slider("Qubit Count (N)", min_value=2, max_value=8, value=4)
        k_target = st.slider("Target K", min_value=1, max_value=n_qubits, value=2)

        run_noise_btn = st.button("🚀 Run Noise Experiment", type="primary", use_container_width=True)

    mu = compute_expected_returns(returns_df.iloc[:, :n_qubits])
    cov = compute_covariance_matrix(returns_df.iloc[:, :n_qubits])
    meta = clean_meta.iloc[:n_qubits]

    Q, offset, _ = build_qubo_matrix(mu, cov, k_target, metadata_df=meta)

    with col2:
        st.info("""
        **Simulation Disclaimer**:
        This experiment evaluates QAOA on a local CPU simulator (`qiskit_aer.AerSimulator`) using a synthetic depolarizing noise model.
        Physical NISQ hardware performance will differ based on connectivity, pulse control, and readout fidelity.
        """)

    st.divider()

    if run_noise_btn:
        with st.spinner("Executing ideal vs noisy QAOA simulation..."):
            noise_results = run_noise_sensitivity_experiment(
                Q=Q,
                offset=offset,
                k_target=k_target,
                depolarizing_p1=p1,
                depolarizing_p2=p2,
                shots=1024,
                seed=42
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ideal Feasible Rate", f"{noise_results['ideal_feasible_rate'] * 100.0:.1f}%")
            m2.metric("Noisy Feasible Rate", f"{noise_results['noisy_feasible_rate'] * 100.0:.1f}%")
            m3.metric("Fidelity Drop", f"{noise_results['fidelity_drop_pct']:.1f}%")
            m4.metric("Noisy Best Cost", f"{noise_results['noisy_best_cost']:.4f}")

            st.json(noise_results)
    else:
        st.info("Click **Run Noise Experiment** above to initiate noise sensitivity analysis.")
