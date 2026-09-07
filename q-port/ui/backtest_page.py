"""
Walk-Forward Backtesting UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_market_data
from core.backtest import run_walk_forward_backtest


def render_backtest_page():
    st.title("⏳ Walk-Forward Backtesting Engine")
    st.caption("Out-of-sample portfolio performance evaluation strictly eliminating look-ahead bias.")

    st.warning("⚠️ **Mandatory Disclaimer**: Past performance is not indicative of future results. Backtests demonstrate historical strategy behavior under historical market dynamics.")

    prices_df, meta_df, _ = get_cached_market_data(force_bundled=True)

    col1, col2 = st.columns(2)
    with col1:
        train_days = st.slider("In-Sample Training Window (Days)", min_value=126, max_value=504, value=252, step=63)
    with col2:
        test_days = st.slider("Out-of-Sample Rebalance Window (Days)", min_value=21, max_value=126, value=63, step=21)

    k_target = st.number_input("Target Portfolio Size (K)", min_value=2, max_value=15, value=5)

    if st.button("🚀 Execute Walk-Forward Backtest", type="primary", use_container_width=True):
        with st.spinner("Running walk-forward backtest across historical rebalance periods..."):
            equity_df, metrics_df, btest_info = run_walk_forward_backtest(
                prices_df=prices_df,
                metadata_df=meta_df,
                k_target=k_target,
                train_window_days=train_days,
                test_window_days=test_days
            )

            st.session_state["backtest_equity"] = equity_df
            st.session_state["backtest_metrics"] = metrics_df
            st.session_state["backtest_info"] = btest_info

    if "backtest_equity" in st.session_state:
        equity_df = st.session_state["backtest_equity"]
        metrics_df = st.session_state["backtest_metrics"]
        btest_info = st.session_state["backtest_info"]

        st.subheader("Out-of-Sample Equity Curves (Growth of ₹1.00)")
        fig_equity = px.line(
            equity_df,
            x=equity_df.index,
            y=equity_df.columns,
            title="Out-of-Sample Portfolio Cumulative Return Curves"
        )
        fig_equity.update_layout(height=450, legend_title="Strategy")
        st.plotly_chart(fig_equity, use_container_width=True)

        st.divider()

        st.subheader("Out-of-Sample Performance Summary Table")
        st.dataframe(metrics_df, use_container_width=True)
