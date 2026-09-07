"""
QUBO Construction & Penalty Calibration UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.qubo import build_qubo_matrix, evaluate_qubo_cost


def render_qubo_page():
    st.title("🧮 QUBO Construction & Penalty Calibration Engine")
    st.caption("Formulate portfolio optimization as a Quadratic Unconstrained Binary Optimization problem.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("QUBO Hyperparameters")
        risk_aversion = st.slider("Risk Aversion (λ)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
        k_target = st.number_input("Target Selection Cardinality (K)", min_value=1, max_value=len(clean_prices.columns), value=5)
        
        penalty_mult = st.slider("Penalty Multiplier (α)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)

    # Subset for visualization clarity if N > 15
    viz_n = min(15, len(mu))
    mu_viz = mu[:viz_n]
    cov_viz = cov[:viz_n, :viz_n]
    meta_viz = clean_meta.iloc[:viz_n]

    Q, offset, qubo_info = build_qubo_matrix(
        expected_returns=mu_viz,
        cov_matrix=cov_viz,
        k_target=k_target if k_target <= viz_n else viz_n // 2,
        risk_aversion=risk_aversion,
        penalty_multiplier=penalty_mult,
        metadata_df=meta_viz
    )

    with col2:
        st.subheader("Calibrated Formulation Parameters")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Dimension (N)", viz_n)
        m2.metric("Target K", qubo_info["k_target"])
        m3.metric("Penalty A", f"{qubo_info['penalty_A']:.4f}")
        m4.metric("Penalty B", f"{qubo_info['penalty_B']:.4f}")

        st.markdown(f"**Constant QUBO Offset**: `{qubo_info['offset']:.4f}`")
        if qubo_info["sector_targets"]:
            st.json({"Sector Target Allocations (K_s)": qubo_info["sector_targets"]})

    st.divider()

    # QUBO Matrix Heatmap
    st.subheader("QUBO Matrix Q (N x N Upper Triangular / Symmetric)")
    fig_q = px.imshow(
        Q,
        color_continuous_scale="Viridis",
        title=f"QUBO Matrix Q ({viz_n} x {viz_n})",
        labels=dict(x="Asset Index j", y="Asset Index i", color="Cost Q_ij")
    )
    fig_q.update_layout(height=450)
    st.plotly_chart(fig_q, use_container_width=True)

    # Interactive Cost Calculator
    st.divider()
    st.subheader("Interactive QUBO Cost Evaluator")
    st.caption("Toggle binary selection for assets and observe direct QUBO cost calculation C(x) = x^T Q x + offset.")

    tickers_viz = list(clean_meta["Ticker"].iloc[:viz_n])
    selected_binary = st.multiselect("Select Active Assets for Vector x:", tickers_viz, default=tickers_viz[:qubo_info["k_target"]])

    x_vec = np.zeros(viz_n, dtype=int)
    for idx, t in enumerate(tickers_viz):
        if t in selected_binary:
            x_vec[idx] = 1

    computed_cost = evaluate_qubo_cost(x_vec, Q, offset)
    k_selected = int(np.sum(x_vec))

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Count (K_selected)", k_selected, delta=k_selected - qubo_info["k_target"])
    c2.metric("QUBO Objective Cost C(x)", f"{computed_cost:.6f}")
    c3.metric("Feasible Cardinality?", "✅ YES" if k_selected == qubo_info["k_target"] else "❌ NO (Penalty Active)")
