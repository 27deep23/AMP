"""
Research Methodology & Mathematical Foundations UI for Q-PORT.
"""

import streamlit as st


def render_methodology_page():
    st.title("📚 Research Methodology & Mathematical Foundations")
    st.caption("Comprehensive technical reference for Q-PORT mathematical formulations, algorithms, and limitations.")

    st.markdown(r"""
    ## 1. Problem Formulation (Markowitz Mean-Variance)
    
    The classical Markowitz portfolio optimization problem seeks to maximize expected return $\mu_p$ while minimizing variance $\sigma_p^2$ subject to constraints:

    $$\max_{w} \quad w^T \mu - \lambda w^T \Sigma w$$
    $$\text{s.t.} \quad \sum_{i=1}^N w_i = 1, \quad 0 \le w_i \le w_{\text{max}}$$

    where $\mu \in \mathbb{R}^N$ is the vector of annualized expected returns, $\Sigma \in \mathbb{R}^{N \times N}$ is the annualized covariance matrix, $\lambda > 0$ is the risk aversion parameter, and $w \in \mathbb{R}^N$ is the continuous allocation vector.

    ---

    ## 2. QUBO Formulation (Stage A Asset Selection)

    Q-PORT converts discrete asset selection into a Quadratic Unconstrained Binary Optimization (QUBO) problem over binary variables $x \in \{0, 1\}^N$:

    $$C(x) = -\left( \frac{\mu^T x}{K} - \lambda \frac{x^T \Sigma x}{K^2} \right) + A \left( \sum_{i=1}^N x_i - K \right)^2 + B \sum_{s=1}^S \left( \sum_{i \in \text{Sector}_s} x_i - K_s \right)^2$$

    where $K = \text{round}((K_{\text{min}} + K_{\text{max}})/2)$ is the target integer asset count, $K_s$ is the sector target allocation (computed via largest-remainder method), and $A, B$ are penalty coefficients dynamically calibrated against the objective swing bound:

    $$\text{swing} = \max(\mu) - \min(\mu) + \lambda \max(\text{diag}(\Sigma)), \quad A = B = 2.0 \times \text{swing}$$

    Expanding the quadratic terms yields the matrix form:
    
    $$C(x) = x^T Q x + \text{offset}$$

    ---

    ## 3. Ising Mapping & QAOA Quantum Engine

    Binary variables $x_i \in \{0, 1\}$ are mapped to Pauli-Z spin operators $Z_i \in \{+1, -1\}$ via $x_i = \frac{1 - Z_i}{2}$, transforming the QUBO matrix $Q$ into an Ising spin Hamiltonian:

    $$H_C = \sum_{i=1}^N h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + \text{offset}_{\text{Ising}}$$

    The QAOA circuit applies alternating cost unitaries $U(H_C, \gamma) = e^{-i \gamma H_C}$ and mixer unitaries $U(H_M, \beta) = e^{-i \beta \sum X_i}$ for $p$ layers starting from the uniform superposition $|+\rangle^{\otimes N}$:

    $$|\psi(\vec{\gamma}, \vec{\beta})\rangle = \prod_{k=1}^p e^{-i \beta_k H_M} e^{-i \gamma_k H_C} |+\rangle^{\otimes N}$$

    The classical outer-loop optimizer (COBYLA) tunes $(\vec{\gamma}, \vec{\beta})$ to minimize $\langle H_C \rangle$.

    ---

    ## 4. Stage B Continuous Weight Allocation

    Once binary asset selection $x \in \{0, 1\}^N$ is established by Stage A (QAOA or classical baseline), continuous weights $w_S$ over the selected subset $S = \{i \mid x_i = 1\}$ are optimized using `scipy.optimize.minimize(method='SLSQP')`:

    $$\min_{w_S} \quad -\left( w_S^T \mu_S - \lambda w_S^T \Sigma_S w_S \right)$$
    $$\text{s.t.} \quad \sum_{j \in S} w_j = 1.0, \quad 0 \le w_j \le w_{\text{max}}, \quad \sum_{j \in \text{Sector}_s} w_j \le \text{max\_sector\_weight}$$

    ---

    ## 5. Platform Limitations & Ethical Disclosure

    > [!IMPORTANT]
    > 1. **Simulator Execution**: QAOA is executed on a local CPU simulator (`qiskit_aer.AerSimulator`). No physical NISQ hardware execution is claimed or performed.
    > 2. **Qubit Limit**: QAOA execution is restricted to $N \le 24$ qubits to prevent CPU RAM exhaustion.
    > 3. **Exact Solver Limit**: Exact enumeration is capped at $2^{22}$ states (approx 4.19M combinations) and 10.0s wall-clock time.
    > 4. **No Financial Advice**: Q-PORT is an educational and research platform. Outputs do not constitute financial advice.

    ---

    ## 6. Dataset Licensing & Reproducibility

    The bundled dataset (`data/sample_assets.csv` and `data/sample_prices.csv`) contains 30 Indian large-cap equities (NSE/BSE) processed for offline reproducible benchmarking in Judge Mode.
    """)
