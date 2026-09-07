"""
Caching utilities for Streamlit app state management in Q-PORT.
"""

import streamlit as st
from core.data_loader import fetch_market_data
from core.preprocessing import preprocess_data


@st.cache_data(show_spinner=False)
def get_cached_market_data(force_bundled: bool = False):
    """Caches data loading to prevent redundant network fetches."""
    return fetch_market_data(force_bundled=force_bundled)


@st.cache_data(show_spinner=False)
def get_cached_preprocessed_data(force_bundled: bool = False):
    """Caches preprocessed daily returns and aligned metadata."""
    prices_df, meta_df, quality_report = get_cached_market_data(force_bundled=force_bundled)
    clean_prices, returns_df, clean_meta, prep_stats = preprocess_data(prices_df, meta_df)
    return clean_prices, returns_df, clean_meta, quality_report, prep_stats
