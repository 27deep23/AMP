"""
Constraint validation module for Q-PORT.
Performs pre-flight mathematical feasibility checks on asset bounds, continuous weights,
sector limits, target returns, target volatility, and integer K selection targets.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from utils.validation import InfeasibleConstraintError, InvalidParameterError


def validate_optimization_config(
    k_min: int,
    k_max: int,
    total_assets: int,
    max_weight: float = 1.0,
    min_weight: float = 0.0,
    max_sector_weight: float = 1.0,
    target_return: Optional[float] = None,
    target_volatility: Optional[float] = None,
    expected_returns: Optional[np.ndarray] = None,
    volatilities: Optional[np.ndarray] = None,
    metadata_df: Optional[pd.DataFrame] = None
) -> Tuple[bool, List[str], List[str], Dict[str, Any]]:
    """
    Validates mathematical feasibility of optimization parameters.
    
    Returns:
        is_valid: bool
        errors: List[str] of explicit failure reasons
        warnings: List[str] of cautionary notices
        params: Dict of computed/validated parameters (e.g. integer target K)
    """
    errors: List[str] = []
    warnings: List[str] = []
    params: Dict[str, Any] = {}

    # 1. Bounds checks on total_assets
    if total_assets < 2:
        errors.append(f"Total asset count ({total_assets}) is less than minimum required (2).")

    # 2. Asset selection bounds (k_min, k_max)
    if k_min < 1:
        errors.append(f"Minimum asset selection count k_min={k_min} must be >= 1.")
    if k_max > total_assets:
        errors.append(f"Maximum asset selection count k_max={k_max} exceeds available assets N={total_assets}.")
    if k_min > k_max:
        errors.append(f"Invalid asset range: k_min ({k_min}) > k_max ({k_max}).")

    # Target integer K calculation
    k_target_float = (k_min + k_max) / 2.0
    if not np.isclose(k_target_float, round(k_target_float)):
        errors.append(
            f"Non-integer asset cardinality target K: (k_min + k_max) / 2 = {k_target_float}. "
            f"k_min ({k_min}) and k_max ({k_max}) must sum to an even number."
        )
    k_target_int = int(round(k_target_float))
    params["target_k"] = k_target_int
    params["k_min"] = k_min
    params["k_max"] = k_max

    # 3. Maximum continuous weight feasibility
    # If max_weight * k_max < 1.0, sum of weights across at most k_max assets cannot equal 1.0
    if k_max > 0 and (max_weight * k_max) < 1.0 - 1e-6:
        min_max_weight_needed = 1.0 / k_max
        errors.append(
            f"Infeasible weight limit: max_weight={max_weight:.1%} across at most K_max={k_max} assets "
            f"can sum to at most {max_weight * k_max:.1%}, which cannot reach 100% total capital. "
            f"Minimum max_weight required is {min_max_weight_needed:.1%}."
        )

    # 4. Sector capacity check
    if metadata_df is not None and "Sector" in metadata_df.columns and k_min > 0:
        sector_counts = metadata_df["Sector"].value_counts().to_dict()
        max_single_sector_assets = max(sector_counts.values()) if sector_counts else 0
        # If max_sector_weight is too restrictive given available sector distribution
        if max_sector_weight * len(sector_counts) < 1.0 - 1e-6:
            errors.append(
                f"Infeasible sector weight limit: max_sector_weight={max_sector_weight:.1%} across "
                f"{len(sector_counts)} sectors cannot sum to 100% total portfolio weight."
            )

    # 5. Target Return feasibility
    if target_return is not None and expected_returns is not None and len(expected_returns) > 0:
        max_possible_ret = float(np.max(expected_returns))
        if target_return > max_possible_ret + 1e-6:
            errors.append(
                f"Unattainable target return: Requested return {target_return:.1%} exceeds the "
                f"maximum expected return among all selected assets ({max_possible_ret:.1%})."
            )

    # 6. Target Volatility feasibility
    if target_volatility is not None and volatilities is not None and len(volatilities) > 0:
        min_asset_vol = float(np.min(volatilities))
        # Note: diversification can lower portfolio vol below min asset vol, but if target_vol is unrealistically low (e.g. <= 0)
        if target_volatility <= 0:
            errors.append(f"Invalid target volatility {target_volatility:.1%}. Must be positive.")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, params


def enforce_valid_config(
    k_min: int,
    k_max: int,
    total_assets: int,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function that raises InfeasibleConstraintError or InvalidParameterError if config is invalid.
    """
    is_valid, errors, warnings, params = validate_optimization_config(
        k_min=k_min,
        k_max=k_max,
        total_assets=total_assets,
        **kwargs
    )
    if not is_valid:
        raise InfeasibleConstraintError(" | ".join(errors))
    return params
