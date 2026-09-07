"""
Q-PORT Portfolio Optimizer Page
================================
Main optimization interface where users configure parameters and run
the full Stage A → Stage B pipeline.
"""
from __future__ import annotations

import streamlit as st

from config.settings import (
    QPortConfig,
    RISK_PROFILES,
    ALLOWED_NUM_ASSETS,
    ALLOWED_MAX_WEIGHT,
    ALLOWED_MAX_SECTOR_WEIGHT,
    ALLOWED_QAOA_P,
    ALLOWED_SHOTS,
    ALLOWED_MAX_ITERATIONS,
)


def render_optimizer() -> None:
    """Render the portfolio optimizer configuration and execution page."""

    st.markdown("### ⚙️ Portfolio Optimizer")
    st.markdown(
        "Configure optimization parameters and run the hybrid "
        "quantum-classical pipeline."
    )

    # --- Configuration sidebar ---
    with st.expander("🔧 Optimization Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Financial**")
            capital = st.number_input(
                "Capital (₹)",
                min_value=100_000.0,
                max_value=100_000_000.0,
                value=10_00_000.0,
                step=100_000.0,
                format="%.0f",
            )
            risk_profile = st.selectbox(
                "Risk Profile",
                options=list(RISK_PROFILES.keys()),
                index=1,
            )
            risk_free_rate = st.number_input(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=6.5,
                step=0.5,
            )

        with col2:
            st.markdown("**Asset Selection**")
            num_assets = st.slider(
                "Universe Size",
                min_value=ALLOWED_NUM_ASSETS[0],
                max_value=ALLOWED_NUM_ASSETS[1],
                value=20,
            )
            min_assets = st.number_input(
                "Min Selected Assets",
                min_value=2,
                max_value=num_assets,
                value=10,
            )
            max_assets = st.number_input(
                "Max Selected Assets",
                min_value=int(min_assets),
                max_value=num_assets,
                value=20,
            )
            # Show computed K
            k_raw = (min_assets + max_assets) / 2
            if k_raw == int(k_raw):
                st.success(f"Fixed cardinality K = {int(k_raw)}")
            else:
                st.error(
                    f"K = {k_raw} is not an integer. "
                    "Adjust min/max so (min + max) / 2 is a whole number."
                )

        with col3:
            st.markdown("**Constraints**")
            max_weight = st.slider(
                "Max Weight per Asset (%)",
                min_value=int(ALLOWED_MAX_WEIGHT[0] * 100),
                max_value=int(ALLOWED_MAX_WEIGHT[1] * 100),
                value=10,
            )
            max_sector_weight = st.slider(
                "Max Sector Weight (%)",
                min_value=int(ALLOWED_MAX_SECTOR_WEIGHT[0] * 100),
                max_value=int(ALLOWED_MAX_SECTOR_WEIGHT[1] * 100),
                value=30,
            )

    with st.expander("⚛️ QAOA Parameters"):
        qcol1, qcol2, qcol3 = st.columns(3)

        with qcol1:
            qaoa_p = st.slider(
                "QAOA Depth (p)",
                min_value=ALLOWED_QAOA_P[0],
                max_value=ALLOWED_QAOA_P[1],
                value=2,
            )
            shots = st.select_slider(
                "Shots",
                options=[512, 1024, 2048, 4096, 8192],
                value=2048,
            )

        with qcol2:
            qaoa_optimizer = st.selectbox(
                "Classical Optimizer",
                options=["COBYLA", "SPSA"],
                index=0,
            )
            max_iterations = st.slider(
                "Max Iterations",
                min_value=ALLOWED_MAX_ITERATIONS[0],
                max_value=ALLOWED_MAX_ITERATIONS[1],
                value=200,
                step=50,
            )

        with qcol3:
            seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=99999,
                value=42,
            )
            use_bundled = st.checkbox(
                "Use Bundled Dataset",
                value=False,
                help="Use deterministic bundled data for reproducibility.",
            )

    st.markdown("---")

    # --- Run optimization ---
    run_clicked = st.button(
        "🚀 Run Optimization",
        type="primary",
        use_container_width=True,
    )

    if run_clicked:
        st.info(
            "🔧 The optimization pipeline will be connected in Phases 2–6. "
            "This page currently validates the configuration UI.",
            icon="🏗️",
        )
