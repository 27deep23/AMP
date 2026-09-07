"""
Unit tests for Research Summary Generator (core/research_summary.py).
"""

import pytest
import pandas as pd
from core.research_summary import generate_research_summary, check_banned_claims


def test_banned_claims_detector():
    """Verify check_banned_claims detects prohibited marketing phrases."""
    clean_text = "Q-PORT evaluates QAOA on a local CPU simulator. NISQ hardware performance will differ."
    assert len(check_banned_claims(clean_text)) == 0

    dirty_text = "This platform proves quantum supremacy and guaranteed quantum speedup for production finance."
    detected = check_banned_claims(dirty_text)
    assert "quantum supremacy" in detected
    assert "guaranteed quantum speedup" in detected


def test_research_summary_generation():
    """Verify research summary generation produces valid markdown with required limitation notice."""
    results_df = pd.DataFrame([
        {
            "Method": "QAOA (Quantum)",
            "Stage-A QUBO Cost": -0.150,
            "Optimality Gap (%)": 5.0,
            "Expected Return (%)": 18.5,
            "Annual Volatility (%)": 15.2,
            "Sharpe Ratio": 0.82,
            "Max Drawdown (%)": 12.0,
            "HHI Index": 0.20,
            "Active Assets": 5,
            "Feasible": True,
            "Runtime (s)": 1.20,
            "Selected Assets": "T1, T2, T3, T4, T5"
        },
        {
            "Method": "Greedy",
            "Stage-A QUBO Cost": -0.158,
            "Optimality Gap (%)": 0.0,
            "Expected Return (%)": 19.1,
            "Annual Volatility (%)": 14.8,
            "Sharpe Ratio": 0.88,
            "Max Drawdown (%)": 11.5,
            "HHI Index": 0.20,
            "Active Assets": 5,
            "Feasible": True,
            "Runtime (s)": 0.05,
            "Selected Assets": "T1, T2, T3, T4, T6"
        }
    ])

    info = {
        "n_assets": 15,
        "k_target": 5,
        "reference_baseline_name": "Best Classical Heuristic"
    }

    summary_md = generate_research_summary(results_df, info)

    assert "# Q-PORT Research Summary" in summary_md
    assert "Scenario B (Classical Outperforms QAOA)" in summary_md
    assert "Mandatory Limitation Disclosure" in summary_md
    assert len(check_banned_claims(summary_md)) == 0
