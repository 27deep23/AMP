"""
Research Summary Generator for Q-PORT.
Generates research-grade summary reports strictly matching empirical benchmark outcomes.
Includes strict banned-claims filter to prevent exaggerated quantum advantage statements.
"""

import pandas as pd
from typing import Dict, Any, List

BANNED_CLAIMS = [
    "quantum supremacy",
    "quantum advantage proven",
    "q-port proves quantum advantage",
    "qaoa guarantees quantum speedup",
    "quantum is faster than classical",
    "quantum superiority is demonstrated",
    "outperforms classical algorithms across all financial domains",
    "guaranteed quantum speedup",
    "replaces classical optimization"
]


def check_banned_claims(text: str) -> List[str]:
    """Scans text for prohibited marketing claims. Returns list of detected banned claims."""
    detected = []
    text_lower = text.lower()
    for claim in BANNED_CLAIMS:
        if claim in text_lower:
            detected.append(claim)
    return detected


def generate_research_summary(
    results_df: pd.DataFrame,
    benchmark_info: Dict[str, Any]
) -> str:
    """
    Generates markdown research report based on empirical benchmark results.
    """
    n = benchmark_info.get("n_assets", 15)
    k = benchmark_info.get("k_target", 5)
    ref_name = benchmark_info.get("reference_baseline_name", "Best Classical Heuristic")

    # Find QAOA, Greedy, SA, and Exact rows if present
    qaoa_row = results_df[results_df["Method"] == "QAOA (Quantum)"]
    greedy_row = results_df[results_df["Method"] == "Greedy"]
    sa_row = results_df[results_df["Method"] == "Simulated Annealing"]
    exact_row = results_df[results_df["Method"] == "Exact Enumeration"]

    qaoa_cost = qaoa_row["Stage-A QUBO Cost"].values[0] if not qaoa_row.empty else None
    greedy_cost = greedy_row["Stage-A QUBO Cost"].values[0] if not greedy_row.empty else None
    sa_cost = sa_row["Stage-A QUBO Cost"].values[0] if not sa_row.empty else None
    qaoa_feasible = qaoa_row["Feasible"].values[0] if not qaoa_row.empty else False

    # Determine Scenario
    if qaoa_cost is not None and qaoa_feasible:
        best_classical_cost = min([c for c in [greedy_cost, sa_cost] if c is not None]) if (greedy_cost or sa_cost) else qaoa_cost
        if qaoa_cost <= best_classical_cost + 1e-6:
            scenario = "Scenario A (QAOA Competitive)"
            finding = f"QAOA achieved a QUBO objective cost ({qaoa_cost:.4f}) competitive with classical heuristics ({best_classical_cost:.4f})."
        else:
            scenario = "Scenario B (Classical Outperforms QAOA)"
            finding = f"Classical heuristics achieved a lower QUBO cost ({best_classical_cost:.4f}) than QAOA ({qaoa_cost:.4f}) on this instance."
    else:
        scenario = "Scenario C (QAOA Infeasible / Skipped)"
        finding = "QAOA did not sample a feasible binary solution matching target cardinality K, or was skipped due to qubit limits."

    report = f"""# Q-PORT Research Summary & Benchmark Findings

## Executive Summary

- **Asset Universe Size (N)**: {n}
- **Target Portfolio Size (K)**: {k}
- **Reference Baseline**: {ref_name}
- **Empirical Scenario Outcome**: **{scenario}**

### Key Empirical Finding
{finding}

---

## Detailed Benchmark Results

{results_df.to_markdown(index=False)}

---

## Methodological Analysis

1. **QUBO Formulation**: The asset selection problem was formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem incorporating Markowitz proxy return and risk terms along with integer cardinality penalties and sector capacity bounds.
2. **Hybrid 2-Stage Allocation**: All algorithms (QAOA, Greedy, Simulated Annealing, Exact Enumeration) were evaluated under identical Stage-B continuous allocation rules using SciPy SLSQP. This guarantees fair comparative evaluation.
3. **Execution Environment**: QAOA was executed on a local CPU simulator (Qiskit Aer).

---

## Limitations & Reproducibility Notice

> **Mandatory Limitation Disclosure**:
> Results presented in this report were obtained using a local CPU simulator (`qiskit_aer.AerSimulator`). NISQ physical hardware performance will differ due to gate infidelity, thermal relaxation, and decoherence. This evaluation demonstrates hybrid quantum-classical workflow integration and algorithmic baseline comparison on ordinary classical hardware.

*Report generated automatically by Q-PORT Platform.*
"""

    # Run security check on banned claims
    violations = check_banned_claims(report)
    if violations:
        raise ValueError(f"Research summary generator produced banned claims: {violations}")

    return report
