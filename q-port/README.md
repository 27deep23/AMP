# Q-PORT

## Quantum Portfolio Intelligence & Optimisation Platform

**UC-018 · Asset Manager Portfolio Optimisation**

Hybrid quantum-classical optimization using quantum simulation on ordinary CPU.

---

## Problem Statement

Given a universe of assets, select an optimal subset and allocate capital to
maximize risk-adjusted return subject to diversification, weight, and sector
constraints. The asset-selection stage is formulated as a QUBO and solved via
QAOA (quantum simulation), then compared against classical baselines under
identical conditions.

### Why This Challenge Matters

Portfolio optimisation with cardinality constraints (selecting *which* assets
to hold) is NP-hard. Traditional mean-variance optimisation assumes continuous
weights across all assets, but real portfolios require discrete decisions:
which assets to include, how many to hold, and how to satisfy regulatory
or risk-management constraints on sector concentration.

### Why Quantum Optimisation Is Relevant — and Where It Isn't, Yet

QAOA is a variational quantum algorithm that can encode combinatorial
optimisation problems naturally. The asset-selection stage maps directly to
a QUBO, making it a candidate for quantum optimization. However:

- Current quantum simulation does not demonstrate general quantum advantage.
- Simulated QAOA performance depends on encoding, circuit depth, and instance size.
- The purpose of Q-PORT is to **measure** competitiveness, not to assume it.

---

## Architecture

```
STREAMLIT UI
│
├── Dashboard            (landing, Judge Mode entry)
├── Portfolio Optimizer   (configuration, execution)
├── Quantum Engine        (QAOA pipeline detail)
├── Classical vs Quantum  (benchmark comparison)
├── Quantum Advantage     (scaling experiments)
├── Noise Sensitivity     (optional noise experiment)
├── Backtesting           (walk-forward backtest)
├── Explainability        (computed explanations)
├── Methodology           (research-grade documentation)
└── Reproducibility       (config export, downloads)

CORE ENGINE
│
├── Data Loader       → yfinance + bundled fallback
├── Statistics        → returns, covariance, Sharpe, CAGR, drawdown
├── Constraints       → pre-flight validation
├── QUBO Builder      → pure quadratic, fixed-K, sector targets
├── Quantum Optimizer → QAOA via Qiskit Aer (simulation only)
├── Classical Optimizer → Greedy, SA, Exact Enumeration
├── Portfolio         → Stage-B SLSQP allocation
├── Benchmark         → fair method comparison
├── Backtest          → walk-forward, no look-ahead
├── Explainability    → computed per-asset analysis
└── Research Summary  → templated conclusions
```

---

## Mathematical Formulation

### Financial Objective

```
max_w  μᵀw − λ wᵀΣw
```

subject to: Σw = 1, w ≤ max_weight, sector constraints, etc.

### QUBO Formulation (Stage A)

```
C(x) = −(proxy_return(x) − λ · proxy_risk(x))
       + A(Σx_i − K)²
       + B Σ_s(Σ_{i∈s} x_i − K_s)²
```

where:
- `proxy_return(x) = μᵀx / K`
- `proxy_risk(x) = xᵀΣx / K²`
- `K = (K_min + K_max) / 2` (must be integer)
- `K_s` = integer sector targets via largest-remainder allocation
- `A`, `B` = penalties calibrated from instance-specific objective swing bound

### QAOA Workflow

```
QUBO → manual Ising conversion (x = (1−z)/2) → QAOA circuit → Aer → measurements → filtering
```

### Classical Baselines

All solve the **identical** QUBO:
- **Greedy**: Fast heuristic
- **Simulated Annealing**: Stochastic combinatorial
- **Exact Enumeration**: Budget-gated exhaustive search

### Benchmark Methodology

All methods evaluated with identical Stage-B allocation (SciPy SLSQP),
identical constraints, identical financial statistics. Gap calculated
relative to Exact Optimum (if available) or Best Known Solution.

### Backtesting Methodology

True walk-forward: for each test period, optimise using only prior data,
freeze portfolio, evaluate on unseen returns. No look-ahead.

---

## Installation

```bash
git clone <repo-url>
cd q-port
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Running Locally

```bash
streamlit run app.py
```

## Deployment

Compatible with Streamlit Community Cloud. Set `is_cloud = True` in
configuration for stricter qubit ceilings.

---

## Limitations

- Current implementation uses quantum simulation, not physical quantum hardware.
- QAOA performance depends strongly on encoding, circuit depth, chosen optimizer, and instance size.
- Current simulations do not establish general quantum advantage.
- Financial estimates depend on historical data and its availability.
- Backtests do not guarantee future performance.
- The Stage-A/Stage-B split introduces an approximation: Stage A selects under an
  equal-weight proxy objective, not the true final objective.
- Larger portfolios become computationally expensive to simulate and are capped
  by the qubit ceiling (stricter still on free-tier cloud hosting).
- Sector-weight and per-asset-weight limits are enforced exactly only in Stage B,
  not inside the QUBO itself.

---

## Future Work

- Execution on real quantum hardware, once accessible and beneficial for this problem class
- Richer, larger asset universes
- Transaction costs and turnover constraints
- ESG constraints
- CVaR / tail-risk optimization
- Multi-period dynamic rebalancing
- Quantum annealing comparison
- Error mitigation
- Larger QUBOs through decomposition
- Hardware-aware circuit compilation
- Statistically rigorous multi-instance benchmarking

---

## Data Licensing Note

Yahoo Finance data retrieved via `yfinance` is used here for
research/demonstration purposes only, via `yfinance`'s unofficial access to
publicly available data. It is not redistributed and is not used for any
commercial trading purpose.

---

## Demo Instructions

1. Launch the application: `streamlit run app.py`
2. Click **RUN 3-MINUTE DEMO** on the Dashboard
3. Judge Mode runs with 15 bundled assets, QAOA p=2, 2048 shots, seed=42
4. Results include: QUBO construction, classical baselines, QAOA simulation,
   Stage-B allocation, benchmark comparison, walk-forward backtest,
   and automated research summary

---

## License

MIT License. See [LICENSE](LICENSE).
