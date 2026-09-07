"""
Statistics engine for Q-PORT.
Computes annualized asset statistics, covariance matrices with epsilon-regularization,
and comprehensive portfolio metrics (return, vol, Sharpe, Max Drawdown, HHI, sector exposure).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple


def compute_expected_returns(
    returns_df: pd.DataFrame,
    annualization_factor: int = 252
) -> np.ndarray:
    """Computes annualized expected return vector (daily mean * 252)."""
    return returns_df.mean().to_numpy() * annualization_factor


def compute_covariance_matrix(
    returns_df: pd.DataFrame,
    annualization_factor: int = 252,
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Computes annualized covariance matrix with epsilon-regularization for numerical stability.
    Sigma_reg = Sigma + epsilon * I
    """
    cov_sample = returns_df.cov().to_numpy() * annualization_factor
    n = cov_sample.shape[0]
    cov_reg = cov_sample + epsilon * np.eye(n)
    return cov_reg


def compute_max_drawdown(daily_returns: np.ndarray) -> Tuple[float, np.ndarray, float]:
    """
    Computes Max Drawdown, cumulative return series, and CAGR from daily returns series.
    Returns (max_drawdown, cumulative_series, cagr)
    """
    if len(daily_returns) == 0:
        return 0.0, np.array([1.0]), 0.0

    cum_series = np.cumprod(1.0 + daily_returns)
    running_max = np.maximum.accumulate(cum_series)
    drawdowns = (running_max - cum_series) / running_max
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    # CAGR calculation
    total_days = len(daily_returns)
    if total_days > 0 and cum_series[-1] > 0:
        cagr = float(cum_series[-1] ** (252.0 / total_days) - 1.0)
    else:
        cagr = 0.0

    return max_dd, cum_series, cagr


def compute_asset_statistics(
    returns_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    risk_free_rate: float = 0.06,
    annualization_factor: int = 252
) -> pd.DataFrame:
    """Computes per-asset summary statistics table."""
    mu = compute_expected_returns(returns_df, annualization_factor)
    cov = compute_covariance_matrix(returns_df, annualization_factor, epsilon=0.0)
    vols = np.sqrt(np.diag(cov))

    records = []
    for idx, col in enumerate(returns_df.columns):
        asset_rets = returns_df[col].to_numpy()
        max_dd, _, _ = compute_max_drawdown(asset_rets)
        sharpe = (mu[idx] - risk_free_rate) / vols[idx] if vols[idx] > 0 else 0.0
        
        # Match metadata
        meta_row = metadata_df[metadata_df["Ticker"] == col]
        name = meta_row["Name"].values[0] if not meta_row.empty else col
        sector = meta_row["Sector"].values[0] if not meta_row.empty else "General"

        records.append({
            "Ticker": col,
            "Name": name,
            "Sector": sector,
            "Expected Return": float(mu[idx]),
            "Annual Volatility": float(vols[idx]),
            "Sharpe Ratio": float(sharpe),
            "Max Drawdown": float(max_dd)
        })

    return pd.DataFrame(records)


def compute_portfolio_stats(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    returns_df: Optional[pd.DataFrame] = None,
    metadata_df: Optional[pd.DataFrame] = None,
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """
    Computes complete performance, risk, and concentration metrics for a portfolio weight vector w.
    """
    w = np.asarray(weights, dtype=float)
    if np.sum(w) > 0 and not np.isclose(np.sum(w), 1.0):
        w = w / np.sum(w)

    port_return = float(np.dot(w, expected_returns))
    port_variance = float(np.dot(w, np.dot(cov_matrix, w)))
    port_vol = float(np.sqrt(max(0.0, port_variance)))
    sharpe = float((port_return - risk_free_rate) / port_vol) if port_vol > 1e-8 else 0.0
    hhi = float(np.sum(w ** 2))

    active_mask = w > 1e-4
    active_count = int(np.sum(active_mask))

    # Sector exposures
    sector_exposures = {}
    if metadata_df is not None and "Sector" in metadata_df.columns:
        sectors = metadata_df["Sector"].tolist()
        for idx, sec in enumerate(sectors):
            sector_exposures[sec] = sector_exposures.get(sec, 0.0) + float(w[idx])

    # Drawdown and CAGR if returns DataFrame provided
    max_dd = 0.0
    cagr = 0.0
    cum_series = np.array([])
    if returns_df is not None and not returns_df.empty:
        port_daily_rets = np.dot(returns_df.to_numpy(), w)
        max_dd, cum_series, cagr = compute_max_drawdown(port_daily_rets)

    return {
        "expected_return": port_return,
        "variance": port_variance,
        "volatility": port_vol,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "hhi": hhi,
        "active_asset_count": active_count,
        "sector_exposures": sector_exposures,
        "weights": w,
        "cumulative_series": cum_series
    }
