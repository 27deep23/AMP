"""
Explainability Engine for Q-PORT.
Decomposes portfolio expected return, variance, marginal risk, and sector allocation down to individual asset contributions.
All explanations trace directly to exact computed covariance and return statistics.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List


def generate_portfolio_explainability(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    metadata_df: pd.DataFrame,
    risk_free_rate: float = 0.06
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes per-asset risk and return attribution table.
    
    Returns:
        attribution_df: Asset-level breakdown of return/variance contribution and marginal risk
        summary_info: High-level explainability summary
    """
    w = np.asarray(weights, dtype=float)
    n = len(w)

    port_ret = float(np.dot(w, expected_returns))
    port_var = float(np.dot(w, np.dot(cov_matrix, w)))
    port_vol = float(np.sqrt(max(1e-12, port_var)))

    # Marginal Contribution to Risk (MCR): (Sigma w)_i / port_vol
    cov_w = np.dot(cov_matrix, w)
    mcr = cov_w / port_vol if port_vol > 0 else np.zeros(n)

    # Component Contribution to Risk (CCR): w_i * MCR_i
    ccr = w * mcr

    # Percentage Contribution to Variance (PCV): w_i * (Sigma w)_i / port_var
    pcv = (w * cov_w) / port_var if port_var > 0 else np.zeros(n)

    # Individual asset volatilities
    asset_vols = np.sqrt(np.diag(cov_matrix))

    records = []
    for i in range(n):
        if w[i] > 1e-4:
            meta_row = metadata_df[metadata_df["Ticker"] == metadata_df.iloc[i]["Ticker"]]
            ticker = metadata_df.iloc[i]["Ticker"]
            name = metadata_df.iloc[i]["Name"] if "Name" in metadata_df.columns else ticker
            sector = metadata_df.iloc[i]["Sector"] if "Sector" in metadata_df.columns else "General"

            ret_contrib = float(w[i] * expected_returns[i])
            ret_contrib_pct = (ret_contrib / port_ret * 100.0) if port_ret != 0 else 0.0

            # Correlation with portfolio: Cov(R_i, R_p) / (sigma_i * sigma_p) = (Sigma w)_i / (sigma_i * sigma_p)
            corr_with_port = float(cov_w[i] / (asset_vols[i] * port_vol)) if (asset_vols[i] > 0 and port_vol > 0) else 0.0

            records.append({
                "Ticker": ticker,
                "Name": name,
                "Sector": sector,
                "Weight (%)": float(w[i] * 100.0),
                "Expected Return (%)": float(expected_returns[i] * 100.0),
                "Return Contribution (%)": ret_contrib * 100.0,
                "Share of Return (%)": ret_contrib_pct,
                "Asset Volatility (%)": float(asset_vols[i] * 100.0),
                "Marginal Risk (MCR)": float(mcr[i]),
                "Variance Contribution (%)": float(pcv[i] * 100.0),
                "Portfolio Correlation": corr_with_port
            })

    attribution_df = pd.DataFrame(records)

    summary_info = {
        "total_active_assets": len(attribution_df),
        "portfolio_expected_return_pct": port_ret * 100.0,
        "portfolio_volatility_pct": port_vol * 100.0,
        "top_return_contributor": attribution_df.sort_values("Return Contribution (%)", ascending=False).iloc[0]["Ticker"] if not attribution_df.empty else "",
        "top_risk_contributor": attribution_df.sort_values("Variance Contribution (%)", ascending=False).iloc[0]["Ticker"] if not attribution_df.empty else ""
    }

    return attribution_df, summary_info
