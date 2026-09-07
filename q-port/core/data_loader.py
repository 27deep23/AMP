"""
Data loader module for Q-PORT.
Fetches historical market data via yfinance with fallbacks to bundled offline dataset.
"""

import os
import time
import logging
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SAMPLE_ASSETS_PATH = os.path.join(DATA_DIR, "sample_assets.csv")
SAMPLE_PRICES_PATH = os.path.join(DATA_DIR, "sample_prices.csv")


def load_bundled_asset_metadata() -> pd.DataFrame:
    """Loads the bundled 30-asset metadata CSV (Ticker, Name, Sector)."""
    if os.path.exists(SAMPLE_ASSETS_PATH):
        return pd.read_csv(SAMPLE_ASSETS_PATH)
    else:
        # Fallback inline default metadata if file missing
        return pd.DataFrame({
            "Ticker": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS"],
            "Name": ["Reliance Industries", "Tata Consultancy Services", "HDFC Bank", "Infosys", "Hindustan Unilever"],
            "Sector": ["Energy", "Technology", "Financials", "Technology", "Consumer Staples"]
        })


def load_bundled_prices() -> pd.DataFrame:
    """Loads the bundled 30-asset daily prices CSV for offline Judge Mode."""
    if os.path.exists(SAMPLE_PRICES_PATH):
        df = pd.read_csv(SAMPLE_PRICES_PATH, index_col=0, parse_dates=True)
        return df
    else:
        # Fallback synthetic prices if file missing
        dates = pd.date_range("2023-01-01", "2025-12-31", freq="B")
        assets = load_bundled_asset_metadata()["Ticker"].tolist()
        np.random.seed(42)
        prices = {}
        for t in assets:
            ret = np.random.normal(0.0005, 0.015, len(dates))
            prices[t] = 100.0 * np.exp(np.cumsum(ret))
        return pd.DataFrame(prices, index=dates)


def fetch_yfinance_ticker(ticker: str, start_date: str, end_date: str) -> Optional[pd.Series]:
    """Fetches close prices for a single ticker with retries."""
    import yfinance as yf
    for attempt in range(2):
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(start=start_date, end=end_date)
            if not hist.empty and "Close" in hist.columns:
                series = hist["Close"].dropna()
                if len(series) > 50:
                    return series
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {ticker}: {e}")
            time.sleep(0.5)
    return None


def fetch_market_data(
    tickers: Optional[List[str]] = None,
    start_date: str = "2023-01-01",
    end_date: str = "2026-01-01",
    force_bundled: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Fetches daily price data and metadata.
    
    Returns:
        prices_df: DataFrame of daily close prices
        metadata_df: DataFrame with columns [Ticker, Name, Sector]
        quality_report: Dict detailing dataset stats, source, dropped tickers
    """
    bundled_meta = load_bundled_asset_metadata()
    bundled_prices = load_bundled_prices()

    if force_bundled or tickers is None:
        selected_tickers = tickers if tickers else bundled_meta["Ticker"].tolist()
        valid_tickers = [t for t in selected_tickers if t in bundled_prices.columns]
        
        prices_df = bundled_prices[valid_tickers].copy()
        metadata_df = bundled_meta[bundled_meta["Ticker"].isin(valid_tickers)].copy()
        
        quality_report = {
            "source": "Bundled Reproducible Dataset (Judge Mode)",
            "requested_count": len(selected_tickers) if tickers else len(bundled_meta),
            "loaded_count": len(valid_tickers),
            "dropped_tickers": list(set(selected_tickers) - set(valid_tickers)) if tickers else [],
            "date_range": (str(prices_df.index[0].date()), str(prices_df.index[-1].date())),
            "total_trading_days": len(prices_df),
            "missing_values_before_clean": int(prices_df.isna().sum().sum())
        }
        return prices_df, metadata_df, quality_report

    # Attempt live download via yfinance
    data_dict = {}
    dropped_tickers = []
    
    for t in tickers:
        series = fetch_yfinance_ticker(t, start_date, end_date)
        if series is not None and not series.empty:
            data_dict[t] = series
        else:
            dropped_tickers.append(t)

    if not data_dict:
        # Complete failure of live fetch -> fallback to bundled
        logger.warning("Live fetch failed for all tickers. Falling back to bundled dataset.")
        return fetch_market_data(tickers=None, force_bundled=True)

    prices_df = pd.DataFrame(data_dict)

    # Build metadata for requested tickers
    meta_records = []
    meta_lookup = dict(zip(bundled_meta["Ticker"], zip(bundled_meta["Name"], bundled_meta["Sector"])))
    
    for t in prices_df.columns:
        if t in meta_lookup:
            name, sector = meta_lookup[t]
        else:
            name = t.split(".")[0]
            sector = "General"
        meta_records.append({"Ticker": t, "Name": name, "Sector": sector})

    metadata_df = pd.DataFrame(meta_records)

    quality_report = {
        "source": "Live Market Data via yfinance",
        "requested_count": len(tickers),
        "loaded_count": len(prices_df.columns),
        "dropped_tickers": dropped_tickers,
        "date_range": (str(prices_df.index[0].date()), str(prices_df.index[-1].date())),
        "total_trading_days": len(prices_df),
        "missing_values_before_clean": int(prices_df.isna().sum().sum())
    }

    return prices_df, metadata_df, quality_report
