"""
Data Management UI for Q-PORT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.caching import get_cached_preprocessed_data, get_cached_market_data
from core.statistics import compute_asset_statistics, compute_expected_returns, compute_covariance_matrix


def render_data_page():
    st.title("📈 Asset Universe & Data Quality Center")
    st.caption("Inspect live market data or bundled reproducible offline dataset for Judge Mode.")

    col1, col2 = st.columns([1, 2])
    with col1:
        data_source = st.radio(
            "Data Ingestion Source",
            ["Bundled Offline Dataset (Judge Mode)", "Live Market Data (yfinance)"],
            index=0
        )
        force_bundled = (data_source == "Bundled Offline Dataset (Judge Mode)")

    clean_prices, returns_df, clean_meta, quality_report, prep_stats = get_cached_preprocessed_data(force_bundled=force_bundled)

    with col2:
        st.subheader("Data Quality Report")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Data Source", quality_report["source"].split(" ")[0])
        m2.metric("Asset Count (N)", prep_stats["final_asset_count"])
        m3.metric("Trading Days", prep_stats["returns_count"])
        m4.metric("Missing Values", quality_report["missing_values_before_clean"])

    st.divider()

    # Asset Universe Selection
    st.subheader("Asset Selection & Sector Exposure")
    all_tickers = list(returns_df.columns)
    selected_tickers = st.multiselect(
        "Filter Asset Universe (min 2 required):",
        all_tickers,
        default=all_tickers[:15]
    )

    if len(selected_tickers) < 2:
        st.error("Please select at least 2 assets for portfolio optimization.")
        return

    sub_returns = returns_df[selected_tickers]
    sub_meta = clean_meta[clean_meta["Ticker"].isin(selected_tickers)]

    # Normalized Price Performance Chart
    st.markdown("#### Historical Price Performance (Normalized to 100)")
    norm_prices = (clean_prices[selected_tickers] / clean_prices[selected_tickers].iloc[0]) * 100.0
    fig_price = px.line(
        norm_prices,
        x=norm_prices.index,
        y=selected_tickers,
        title="Normalized Asset Growth (Base = 100)"
    )
    fig_price.update_layout(height=420, legend_title="Ticker")
    st.plotly_chart(fig_price, use_container_width=True)

    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.markdown("#### Per-Asset Summary Statistics Table")
        asset_stats = compute_asset_statistics(sub_returns, sub_meta)
        st.dataframe(asset_stats, use_container_width=True)

    with col_t2:
        st.markdown("#### Asset Correlation Heatmap")
        corr_matrix = sub_returns.corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            title="Correlation Matrix"
        )
        fig_corr.update_layout(height=420)
        st.plotly_chart(fig_corr, use_container_width=True)
