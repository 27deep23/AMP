"""
FastAPI Backend Server for Q-PORT.
Exposes clean REST API endpoints serving portfolio optimization, benchmarking, backtesting,
and plain-English explainability to the React frontend.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from core.data_loader import fetch_market_data
from core.preprocessing import preprocess_data
from core.statistics import compute_expected_returns, compute_covariance_matrix, compute_asset_statistics
from core.constraints import validate_optimization_config
from core.qubo import build_qubo_matrix, evaluate_qubo_cost
from core.classical_optimizer import solve_greedy, solve_simulated_annealing, solve_exact_enumeration
from core.quantum_optimizer import solve_qaoa, qubo_to_ising
from core.portfolio import optimize_continuous_weights
from core.benchmark import run_benchmark_suite
from core.backtest import run_walk_forward_backtest
from core.explainability import generate_portfolio_explainability
from core.research_summary import generate_research_summary
from utils.formatting import format_inr, format_pct, format_sec

app = FastAPI(
    title="Q-PORT API",
    description="Quantum Portfolio Intelligence & Optimisation Platform REST API",
    version="2.0.0"
)

# Enable CORS for React frontend (localhost:5173 or localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class OptimizationRequest(BaseModel):
    capital: float = Field(default=1000000.0, description="Capital investment in INR")
    k_target: int = Field(default=5, description="Target asset count")
    risk_aversion: float = Field(default=1.0, description="Risk aversion parameter lambda")
    max_weight: float = Field(default=0.35, description="Maximum weight per asset")
    max_sector_weight: float = Field(default=0.50, description="Maximum sector weight")
    selected_tickers: Optional[List[str]] = Field(default=None, description="Optional custom tickers subset")
    solver: str = Field(default="qaoa", description="qaoa, greedy, sa, or exact")
    force_bundled: bool = Field(default=True, description="Force bundled dataset for Judge Mode")


class BenchmarkRequest(BaseModel):
    n_assets: int = Field(default=15, description="Number of assets in universe")
    k_target: int = Field(default=5, description="Target asset count")
    risk_aversion: float = Field(default=1.0, description="Risk aversion parameter")
    max_weight: float = Field(default=0.35, description="Max weight")
    max_sector_weight: float = Field(default=0.50, description="Max sector weight")
    run_qaoa: bool = Field(default=True, description="Include QAOA solver")
    run_exact: bool = Field(default=True, description="Include exact solver")
    force_bundled: bool = Field(default=True, description="Force bundled dataset")


class BacktestRequest(BaseModel):
    train_window_days: int = Field(default=252, description="In-sample training days")
    test_window_days: int = Field(default=63, description="Out-of-sample test days")
    k_target: int = Field(default=5, description="Target portfolio size")
    force_bundled: bool = Field(default=True, description="Force bundled dataset")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "platform": "Q-PORT Quantum Engine", "version": "2.0.0"}


@app.get("/api/assets")
def get_assets(force_bundled: bool = True):
    prices_df, meta_df, quality_report = fetch_market_data(force_bundled=force_bundled)
    clean_prices, returns_df, clean_meta, prep_stats = preprocess_data(prices_df, meta_df)
    asset_stats = compute_asset_statistics(returns_df, clean_meta)
    
    return {
        "quality_report": quality_report,
        "prep_stats": prep_stats,
        "assets": asset_stats.to_dict(orient="records")
    }


@app.post("/api/optimize")
def optimize_portfolio(req: OptimizationRequest):
    prices_df, meta_df, _ = fetch_market_data(force_bundled=req.force_bundled)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)

    if req.selected_tickers:
        valid_tickers = [t for t in req.selected_tickers if t in returns_df.columns]
        if len(valid_tickers) >= 2:
            returns_df = returns_df[valid_tickers]
            clean_meta = clean_meta[clean_meta["Ticker"].isin(valid_tickers)]

    mu = compute_expected_returns(returns_df)
    cov = compute_covariance_matrix(returns_df)
    n = len(mu)
    k_target = min(req.k_target, n)

    # Validate constraints
    is_valid, errors, warnings, _ = validate_optimization_config(
        k_min=max(1, k_target - 1),
        k_max=min(n, k_target + 1),
        total_assets=n,
        max_weight=req.max_weight,
        max_sector_weight=req.max_sector_weight,
        metadata_df=clean_meta
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=" | ".join(errors))

    # Build QUBO
    Q, offset, qubo_info = build_qubo_matrix(mu, cov, k_target, req.risk_aversion, metadata_df=clean_meta)

    # Solve Stage A
    if req.solver == "qaoa" and n <= 24:
        best_x, best_cost, runtime, solver_metrics = solve_qaoa(Q, offset, k_target, p=1, shots=1024)
    elif req.solver == "sa":
        best_x, best_cost, runtime, solver_metrics = solve_simulated_annealing(Q, offset, k_target)
    elif req.solver == "exact" and n <= 22:
        best_x, best_cost, runtime, solver_metrics = solve_exact_enumeration(Q, offset, k_target)
    else:
        best_x, best_cost, runtime, solver_metrics = solve_greedy(Q, offset, k_target)

    # Solve Stage B continuous weights
    port_stats = optimize_continuous_weights(
        selection_vector=best_x,
        expected_returns=mu,
        cov_matrix=cov,
        risk_aversion=req.risk_aversion,
        max_weight=req.max_weight,
        max_sector_weight=req.max_sector_weight,
        returns_df=returns_df,
        metadata_df=clean_meta
    )

    # Asset attribution
    attr_df, summary_explain = generate_portfolio_explainability(port_stats["weights"], mu, cov, clean_meta)

    # Format allocation details
    allocations = []
    tickers = list(returns_df.columns)
    weights = port_stats["weights"]
    for idx, t in enumerate(tickers):
        if weights[idx] > 1e-4:
            meta_row = clean_meta[clean_meta["Ticker"] == t]
            name = meta_row["Name"].values[0] if not meta_row.empty else t
            sector = meta_row["Sector"].values[0] if not meta_row.empty else "General"
            alloc_amt = weights[idx] * req.capital
            allocations.append({
                "ticker": t,
                "name": name,
                "sector": sector,
                "weight_pct": round(float(weights[idx] * 100.0), 2),
                "allocation_inr": round(float(alloc_amt), 2),
                "formatted_inr": format_inr(alloc_amt)
            })

    # Plain-English Executive Summary ("Why this portfolio?")
    top_stock = allocations[0]["name"] if allocations else "Selected Equities"
    narrative = (
        f"Selected a balanced portfolio of {len(allocations)} equities led by {top_stock}. "
        f"Targeting an annualized return of {port_stats['expected_return']*100.0:.2f}% with a controlled "
        f"volatility of {port_stats['volatility']*100.0:.2f}%, producing a strong Sharpe ratio of {port_stats['sharpe_ratio']:.2f}."
    )

    return {
        "solver": req.solver,
        "runtime_sec": round(runtime, 4),
        "qubo_cost": round(best_cost, 6),
        "metrics": {
            "expected_return_pct": round(port_stats["expected_return"] * 100.0, 2),
            "volatility_pct": round(port_stats["volatility"] * 100.0, 2),
            "sharpe_ratio": round(port_stats["sharpe_ratio"], 2),
            "max_drawdown_pct": round(port_stats["max_drawdown"] * 100.0, 2),
            "hhi_index": round(port_stats["hhi"], 4),
            "active_assets": port_stats["active_asset_count"]
        },
        "allocations": allocations,
        "attribution": attr_df.to_dict(orient="records"),
        "sector_exposures": {k: round(v * 100.0, 2) for k, v in port_stats["sector_exposures"].items()},
        "executive_narrative": narrative
    }


@app.post("/api/benchmark")
def run_benchmark(req: BenchmarkRequest):
    prices_df, meta_df, _ = fetch_market_data(force_bundled=req.force_bundled)
    clean_prices, returns_df, clean_meta, _ = preprocess_data(prices_df, meta_df)

    sub_returns = returns_df.iloc[:, :req.n_assets]
    sub_meta = clean_meta.iloc[:req.n_assets]

    results_df, bench_info = run_benchmark_suite(
        returns_df=sub_returns,
        metadata_df=sub_meta,
        k_target=req.k_target,
        risk_aversion=req.risk_aversion,
        max_weight=req.max_weight,
        max_sector_weight=req.max_sector_weight,
        run_qaoa=req.run_qaoa,
        run_exact=req.run_exact,
        seed=42
    )

    research_md = generate_research_summary(results_df, bench_info)

    return {
        "info": bench_info,
        "results": results_df.to_dict(orient="records"),
        "research_summary": research_md
    }


@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    prices_df, meta_df, _ = fetch_market_data(force_bundled=req.force_bundled)

    equity_df, metrics_df, btest_info = run_walk_forward_backtest(
        prices_df=prices_df,
        metadata_df=meta_df,
        k_target=req.k_target,
        train_window_days=req.train_window_days,
        test_window_days=req.test_window_days
    )

    # Format equity curves for JSON chart plotting
    dates = [str(d.date()) for d in equity_df.index]
    chart_series = []
    for date_str, row in zip(dates, equity_df.to_dict(orient="records")):
        row["date"] = date_str
        chart_series.append(row)

    return {
        "info": btest_info,
        "metrics": metrics_df.to_dict(orient="records"),
        "equity_curves": chart_series
    }
