"""
Constraint Management & Pre-Flight Validation UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data
from core.constraints import validate_optimization_config
from core.statistics import compute_expected_returns, compute_covariance_matrix


def render_constraints_page():
    st.title("⚙️ Constraint Management & Pre-Flight Validation")
    st.caption("Configure portfolio boundaries, asset selection cardinality, and weight limits.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)
    total_available_assets = len(clean_prices.columns)

    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)
    vols = np.sqrt(np.diag(cov))

    st.sidebar.markdown("### 🎛️ Optimization Controls")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Asset Selection Cardinality Bounds")
        k_min = st.number_input("Minimum Assets (K_min)", min_value=1, max_value=total_available_assets, value=3)
        k_max = st.number_input("Maximum Assets (K_max)", min_value=1, max_value=total_available_assets, value=7)
        k_target = int(round((k_min + k_max) / 2.0))

        st.info(f"Target Selection Cardinality (Integer K): **{k_target} assets**")

        st.subheader("Continuous Weight Limits")
        max_weight = st.slider("Maximum Single Asset Weight (w_max)", min_value=0.05, max_value=1.0, value=0.35, step=0.05)
        max_sector_weight = st.slider("Maximum Sector Weight", min_value=0.10, max_value=1.0, value=0.50, step=0.05)

    with col2:
        st.subheader("Financial Performance Targets")
        use_target_ret = st.checkbox("Enable Target Return Constraint")
        target_return = None
        if use_target_ret:
            max_asset_ret = float(np.max(mu))
            target_return = st.slider(
                "Target Return (% p.a.)",
                min_value=0.0,
                max_value=float(max_asset_ret * 100.0),
                value=float(min(15.0, max_asset_ret * 100.0))
            ) / 100.0

        use_target_vol = st.checkbox("Enable Target Volatility Ceiling")
        target_volatility = None
        if use_target_vol:
            min_asset_vol = float(np.min(vols))
            target_volatility = st.slider(
                "Maximum Target Volatility (% p.a.)",
                min_value=float(min_asset_vol * 100.0),
                max_value=40.0,
                value=20.0
            ) / 100.0

        st.subheader("Capital & Currency")
        capital_inr = st.number_input("Portfolio Capital Investment (INR ₹)", min_value=100000, value=1000000, step=100000)

    st.divider()

    # Pre-Flight Feasibility Validation Check
    st.subheader("Pre-Flight Feasibility Diagnostic")

    is_valid, errors, warnings, params = validate_optimization_config(
        k_min=k_min,
        k_max=k_max,
        total_assets=total_available_assets,
        max_weight=max_weight,
        max_sector_weight=max_sector_weight,
        target_return=target_return,
        target_volatility=target_volatility,
        expected_returns=mu,
        volatilities=vols,
        metadata_df=clean_meta
    )

    if is_valid:
        st.success("✅ **Pre-Flight Check Passed**: All specified constraints are mathematically feasible!")
        if warnings:
            for w in warnings:
                st.warning(f"⚠️ {w}")
    else:
        st.error("❌ **Pre-Flight Check Failed**: The current constraint configuration is mathematically INFEASIBLE.")
        for err in errors:
            st.error(f"• {err}")

    # Sector Capacity Chart
    st.divider()
    st.subheader("Sector Asset Distribution")
    sec_counts = clean_meta["Sector"].value_counts().reset_index()
    sec_counts.columns = ["Sector", "Asset Count"]
    fig_sec = px.bar(sec_counts, x="Sector", y="Asset Count", color="Sector", title="Assets per Sector")
    fig_sec.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_sec, use_container_width=True)
