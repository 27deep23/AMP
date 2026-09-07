"""
Portfolio Explainability & Asset Attribution UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.caching import get_cached_preprocessed_data
from core.statistics import compute_expected_returns, compute_covariance_matrix
from core.portfolio import optimize_continuous_weights
from core.qubo import build_qubo_matrix
from core.classical_optimizer import solve_greedy
from core.explainability import generate_portfolio_explainability


def render_explainability_page():
    st.title("🔍 Portfolio Explainability & Asset Attribution")
    st.caption("Decompose portfolio risk, expected return, and sector exposure down to individual asset contributions.")

    clean_prices, returns_df, clean_meta, _, _ = get_cached_preprocessed_data(force_bundled=True)
    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)

    Q, offset, _ = build_qubo_matrix(mu, cov, k_target=5, metadata_df=clean_meta)
    x_greedy, _, _, _ = solve_greedy(Q, offset, k_target=5)
    stats = optimize_continuous_weights(x_greedy, mu, cov, metadata_df=clean_meta)
    weights = stats["weights"]

    attr_df, summary_info = generate_portfolio_explainability(weights, mu, cov, clean_meta)

    st.subheader("Asset Attribution Table")
    st.dataframe(attr_df, use_container_width=True)

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Return Contribution by Asset")
        fig_ret = px.bar(
            attr_df,
            x="Ticker",
            y="Return Contribution (%)",
            color="Sector",
            title="Expected Return Contribution (% p.a.)",
            text_auto=".2f"
        )
        fig_ret.update_layout(height=400)
        st.plotly_chart(fig_ret, use_container_width=True)

    with c2:
        st.markdown("#### Variance Risk Contribution by Asset")
        fig_var = px.pie(
            attr_df,
            names="Ticker",
            values="Variance Contribution (%)",
            title="Share of Portfolio Variance (%)",
            hole=0.4
        )
        fig_var.update_layout(height=400)
        st.plotly_chart(fig_var, use_container_width=True)
