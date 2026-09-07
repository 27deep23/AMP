"""
Q-PORT Configuration Settings
==============================
All default configuration constants for the Q-PORT platform.
These values define the default behavior and can be overridden via the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Capital
# ---------------------------------------------------------------------------
DEFAULT_CAPITAL: float = 10_00_000.0  # ₹10,00,000

# ---------------------------------------------------------------------------
# Risk profiles: name -> lambda (risk aversion)
# ---------------------------------------------------------------------------
RISK_PROFILES: Dict[str, float] = {
    "Conservative": 8.0,
    "Moderate": 4.0,
    "Aggressive": 1.5,
}
DEFAULT_RISK_PROFILE: str = "Moderate"

# ---------------------------------------------------------------------------
# Asset universe
# ---------------------------------------------------------------------------
DEFAULT_NUM_ASSETS: int = 20
ALLOWED_NUM_ASSETS: Tuple[int, int] = (15, 30)
JUDGE_MODE_NUM_ASSETS: int = 15

# ---------------------------------------------------------------------------
# Weight constraints
# ---------------------------------------------------------------------------
DEFAULT_MAX_WEIGHT: float = 0.10       # 10%
ALLOWED_MAX_WEIGHT: Tuple[float, float] = (0.02, 0.25)  # 2%–25%

DEFAULT_MAX_SECTOR_WEIGHT: float = 0.30  # 30%
ALLOWED_MAX_SECTOR_WEIGHT: Tuple[float, float] = (0.10, 0.60)  # 10%–60%

# ---------------------------------------------------------------------------
# Asset selection cardinality
# ---------------------------------------------------------------------------
DEFAULT_MIN_ASSETS: int = 10
DEFAULT_MAX_ASSETS: int = 20

# ---------------------------------------------------------------------------
# Financial parameters
# ---------------------------------------------------------------------------
DEFAULT_RISK_FREE_RATE: float = 0.065   # 6.5%
DEFAULT_HORIZON_YEARS: int = 1
TRADING_DAYS_PER_YEAR: int = 252

# ---------------------------------------------------------------------------
# Covariance regularization
# ---------------------------------------------------------------------------
COVARIANCE_EPSILON: float = 1e-4

# ---------------------------------------------------------------------------
# QAOA parameters
# ---------------------------------------------------------------------------
DEFAULT_QAOA_P: int = 2
ALLOWED_QAOA_P: Tuple[int, int] = (1, 4)

DEFAULT_SHOTS: int = 2048
ALLOWED_SHOTS: Tuple[int, int] = (512, 8192)

DEFAULT_QAOA_OPTIMIZER: str = "COBYLA"
ALTERNATIVE_QAOA_OPTIMIZER: str = "SPSA"

DEFAULT_MAX_ITERATIONS: int = 200
ALLOWED_MAX_ITERATIONS: Tuple[int, int] = (50, 500)

DEFAULT_SEED: int = 42

# ---------------------------------------------------------------------------
# Qubit ceilings
# ---------------------------------------------------------------------------
LOCAL_SOFT_QUBIT_CEILING: int = 20
LOCAL_HARD_QUBIT_CEILING: int = 24

CLOUD_SOFT_QUBIT_CEILING: int = 16
CLOUD_HARD_QUBIT_CEILING: int = 20

# ---------------------------------------------------------------------------
# Penalty calibration
# ---------------------------------------------------------------------------
DEFAULT_PENALTY_MULTIPLIER: float = 2.0

# ---------------------------------------------------------------------------
# Exact solver budget
# ---------------------------------------------------------------------------
EXACT_MAX_STATES: int = 2**22          # 4,194,304
EXACT_MAX_RUNTIME_SECONDS: float = 10.0

# ---------------------------------------------------------------------------
# Judge Mode
# ---------------------------------------------------------------------------
JUDGE_MODE_QAOA_TIMEOUT_SECONDS: float = 90.0
JUDGE_MODE_TOTAL_TIMEOUT_SECONDS: float = 180.0

# ---------------------------------------------------------------------------
# QAOA smoke test
# ---------------------------------------------------------------------------
SMOKE_TEST_MIN_PROBABILITY: float = 0.90

# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------
DEFAULT_BACKTEST_TRAINING_MONTHS: int = 12
DEFAULT_BACKTEST_TEST_MONTHS: int = 3

# ---------------------------------------------------------------------------
# UI / display
# ---------------------------------------------------------------------------
APP_TITLE: str = "Q-PORT"
APP_SUBTITLE: str = "Quantum Portfolio Intelligence & Optimisation Platform"
APP_CHALLENGE: str = "UC-018 · Asset Manager Portfolio Optimisation"
APP_TAGLINE: str = "Hybrid quantum-classical optimization using quantum simulation."

DISCLAIMER: str = (
    "⚠️ **Disclaimer:** Q-PORT is a research/analysis platform. "
    "It does not provide financial advice, execute trades, or connect to "
    "brokerage systems. Past performance does not guarantee future results. "
    "All quantum computation uses simulation on ordinary CPU infrastructure — "
    "no physical quantum hardware is used."
)

DATA_LICENSING_NOTE: str = (
    "Yahoo Finance data retrieved via `yfinance` is used here for "
    "research/demonstration purposes only, via `yfinance`'s unofficial "
    "access to publicly available data. It is not redistributed and is "
    "not used for any commercial trading purpose."
)

# ---------------------------------------------------------------------------
# Page identifiers
# ---------------------------------------------------------------------------
PAGES: List[Dict[str, str]] = [
    {"id": "dashboard",           "icon": "🏛️", "title": "Executive Dashboard"},
    {"id": "data",                "icon": "📈", "title": "Asset Universe & Data Quality"},
    {"id": "constraints",         "icon": "⚙️",  "title": "Constraints & Validation"},
    {"id": "qubo",                "icon": "🧮", "title": "QUBO Matrix Formulation"},
    {"id": "quantum",             "icon": "⚛️",  "title": "QAOA Quantum Engine"},
    {"id": "benchmark",           "icon": "🏆", "title": "Classical vs Quantum Benchmark"},
    {"id": "quantum_advantage",   "icon": "🚀", "title": "Quantum Advantage Explorer"},
    {"id": "noise",               "icon": "🎛️", "title": "Noise Sensitivity & Hardware Limits"},
    {"id": "backtest",            "icon": "⏳", "title": "Walk-Forward Backtest"},
    {"id": "explainability",      "icon": "🔍", "title": "Portfolio Explainability"},
    {"id": "methodology",         "icon": "📚", "title": "Research Methodology"},
    {"id": "reproducibility",     "icon": "💾", "title": "Reproducibility Export Center"},
]


@dataclass
class QPortConfig:
    """Runtime configuration for a Q-PORT optimization run."""

    # Capital
    capital: float = DEFAULT_CAPITAL

    # Risk
    risk_profile: str = DEFAULT_RISK_PROFILE
    risk_aversion: float = RISK_PROFILES[DEFAULT_RISK_PROFILE]

    # Universe
    num_assets: int = DEFAULT_NUM_ASSETS

    # Cardinality
    min_assets: int = DEFAULT_MIN_ASSETS
    max_assets: int = DEFAULT_MAX_ASSETS

    # Weights
    max_weight: float = DEFAULT_MAX_WEIGHT
    max_sector_weight: float = DEFAULT_MAX_SECTOR_WEIGHT

    # Financial
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    horizon_years: int = DEFAULT_HORIZON_YEARS

    # Covariance
    cov_epsilon: float = COVARIANCE_EPSILON

    # QAOA
    qaoa_p: int = DEFAULT_QAOA_P
    shots: int = DEFAULT_SHOTS
    qaoa_optimizer: str = DEFAULT_QAOA_OPTIMIZER
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    seed: int = DEFAULT_SEED

    # Penalties
    penalty_multiplier: float = DEFAULT_PENALTY_MULTIPLIER
    manual_penalty_A: float | None = None
    manual_penalty_B: float | None = None

    # Ceilings
    soft_qubit_ceiling: int = LOCAL_SOFT_QUBIT_CEILING
    hard_qubit_ceiling: int = LOCAL_HARD_QUBIT_CEILING

    # Exact solver
    exact_max_states: int = EXACT_MAX_STATES
    exact_max_runtime_seconds: float = EXACT_MAX_RUNTIME_SECONDS

    # Judge mode
    judge_mode: bool = False
    qaoa_timeout_seconds: float = JUDGE_MODE_QAOA_TIMEOUT_SECONDS

    # Targets (optional constraints)
    target_return: float | None = None
    max_volatility: float | None = None

    # Data
    use_bundled_data: bool = False
    data_period: str = "2y"

    # Environment
    is_cloud: bool = False

    def get_active_soft_ceiling(self) -> int:
        """Return the active soft qubit ceiling based on environment."""
        if self.is_cloud:
            return CLOUD_SOFT_QUBIT_CEILING
        return self.soft_qubit_ceiling

    def get_active_hard_ceiling(self) -> int:
        """Return the active hard qubit ceiling based on environment."""
        if self.is_cloud:
            return CLOUD_HARD_QUBIT_CEILING
        return self.hard_qubit_ceiling

    def compute_K(self) -> int:
        """Compute the fixed cardinality K = (min_assets + max_assets) / 2.

        Raises:
            ValueError: If K is not an integer.
        """
        k_raw = (self.min_assets + self.max_assets) / 2
        if k_raw != int(k_raw):
            raise ValueError(
                f"Minimum ({self.min_assets}) and maximum ({self.max_assets}) "
                f"selected-asset limits produce K = {k_raw}, which is not an "
                f"integer. Adjust limits so that (min + max) / 2 is a whole number."
            )
        return int(k_raw)

    def to_dict(self) -> dict:
        """Serialize configuration for reproducibility export."""
        k_val = self.compute_K()
        return {
            "seed": self.seed,
            "capital": self.capital,
            "risk_profile": self.risk_profile,
            "risk_aversion": self.risk_aversion,
            "lambda": self.risk_aversion,
            "num_assets": self.num_assets,
            "asset_universe": self.num_assets,
            "min_assets": self.min_assets,
            "max_assets": self.max_assets,
            "K": k_val,
            "K_min": self.min_assets,
            "K_max": self.max_assets,
            "max_weight": self.max_weight,
            "max_sector_weight": self.max_sector_weight,
            "risk_free_rate": self.risk_free_rate,
            "horizon_years": self.horizon_years,
            "cov_epsilon": self.cov_epsilon,
            "covariance_epsilon": self.cov_epsilon,
            "qaoa_p": self.qaoa_p,
            "qaoa_parameter_count": 2 * self.qaoa_p,
            "shots": self.shots,
            "optimization_shots": self.shots,
            "final_measurement_shots": self.shots,
            "qaoa_optimizer": self.qaoa_optimizer,
            "max_iterations": self.max_iterations,
            "configured_max_iterations": self.max_iterations,
            "penalty_multiplier": self.penalty_multiplier,
            "manual_penalty_A": self.manual_penalty_A,
            "manual_penalty_B": self.manual_penalty_B,
            "manual_penalty_override": self.manual_penalty_A is not None or self.manual_penalty_B is not None,
            "soft_qubit_ceiling": self.soft_qubit_ceiling,
            "hard_qubit_ceiling": self.hard_qubit_ceiling,
            "active_qubit_ceiling": self.get_active_hard_ceiling(),
            "exact_max_states": self.exact_max_states,
            "exact_max_runtime_seconds": self.exact_max_runtime_seconds,
            "judge_mode": self.judge_mode,
            "qaoa_timeout_seconds": self.qaoa_timeout_seconds,
            "target_return": self.target_return,
            "max_volatility": self.max_volatility,
            "use_bundled_data": self.use_bundled_data,
            "data_source": "yfinance_bundled" if self.use_bundled_data else "yfinance_live",
            "data_period": self.data_period,
            "is_cloud": self.is_cloud,
            "active_soft_ceiling": self.get_active_soft_ceiling(),
            "active_hard_ceiling": self.get_active_hard_ceiling(),
        }
