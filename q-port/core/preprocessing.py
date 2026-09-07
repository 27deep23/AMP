"""
Preprocessing module for Q-PORT.
Cleans price data, computes percentage daily returns, and validates asset counts.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List


def preprocess_data(
    prices_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    min_trading_days: int = 126
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Cleans prices and computes daily returns.
    
    Args:
        prices_df: Raw daily close prices (index: Date, columns: Ticker)
        metadata_df: Asset metadata (Ticker, Name, Sector)
        min_trading_days: Minimum valid price points required per asset
        
    Returns:
        clean_prices: Cleaned daily price DataFrame
        returns_df: Cleaned daily percentage returns DataFrame
        clean_metadata: Aligned metadata DataFrame matching columns of clean_prices
        preprocessing_stats: Dict of preprocessing diagnostics
    """
    if prices_df.empty:
        raise ValueError("Prices DataFrame is empty.")

    # Forward fill then backward fill
    prices_filled = prices_df.ffill().bfill()

    # Drop columns with insufficient history or remaining NaNs
    valid_cols = []
    dropped_cols = []
    for col in prices_filled.columns:
        non_nan_count = prices_filled[col].notna().sum()
        if non_nan_count >= min_trading_days:
            valid_cols.append(col)
        else:
            dropped_cols.append(col)

    if not valid_cols:
        raise ValueError(f"No assets meet the minimum requirement of {min_trading_days} trading days.")

    clean_prices = prices_filled[valid_cols].copy()

    # Calculate percentage daily returns
    returns_df = clean_prices.pct_change().dropna()

    # Align metadata
    clean_metadata = metadata_df[metadata_df["Ticker"].isin(valid_cols)].copy()
    # Reorder metadata rows to match clean_prices columns
    clean_metadata["Ticker"] = pd.Categorical(clean_metadata["Ticker"], categories=valid_cols, ordered=True)
    clean_metadata = clean_metadata.sort_values("Ticker").reset_index(drop=True)
    clean_metadata["Ticker"] = clean_metadata["Ticker"].astype(str)

    preprocessing_stats = {
        "initial_asset_count": len(prices_df.columns),
        "final_asset_count": len(valid_cols),
        "dropped_assets": dropped_cols,
        "returns_count": len(returns_df),
        "start_date": str(returns_df.index[0].date()),
        "end_date": str(returns_df.index[-1].date())
    }

    return clean_prices, returns_df, clean_metadata, preprocessing_stats
