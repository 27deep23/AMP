"""
Unit tests for Q-PORT constraint validation module.
Verifies that infeasible configurations trigger clear, explicit error diagnostics.
"""

import pytest
import numpy as np
import pandas as pd
from core.constraints import validate_optimization_config, enforce_valid_config
from utils.validation import InfeasibleConstraintError


def test_infeasible_weight_bound():
    """
    Infeasible scenario 1: max_weight=0.10, k_max=5.
    Max sum of weights across 5 assets @ 10% each is 50%, which cannot reach 100%.
    """
    is_valid, errors, _, _ = validate_optimization_config(
        k_min=3,
        k_max=5,
        total_assets=15,
        max_weight=0.10  # Infeasible!
    )
    assert not is_valid
    assert any("Infeasible weight limit" in err for err in errors)
    assert any("Minimum max_weight required is 20.0%" in err for err in errors)


def test_unattainable_target_return():
    """
    Infeasible scenario 2: Target return = 50%, highest asset expected return = 25%.
    """
    exp_rets = np.array([0.10, 0.15, 0.20, 0.25])
    is_valid, errors, _, _ = validate_optimization_config(
        k_min=2,
        k_max=4,
        total_assets=4,
        target_return=0.50,  # 50% target return is unattainable
        expected_returns=exp_rets
    )
    assert not is_valid
    assert any("Unattainable target return" in err for err in errors)
    assert any("25.0%" in err for err in errors)


def test_invalid_k_range():
    """
    Infeasible scenario 3: k_min=10 > k_max=5 or k_max > N.
    """
    is_valid, errors, _, _ = validate_optimization_config(
        k_min=10,
        k_max=5,
        total_assets=15
    )
    assert not is_valid
    assert any("k_min (10) > k_max (5)" in err for err in errors)

    is_valid2, errors2, _, _ = validate_optimization_config(
        k_min=5,
        k_max=20,
        total_assets=15  # k_max > total_assets
    )
    assert not is_valid2
    assert any("exceeds available assets N=15" in err for err in errors2)


def test_enforce_valid_config_raises_exception():
    """Verify that enforce_valid_config raises InfeasibleConstraintError on invalid config."""
    with pytest.raises(InfeasibleConstraintError) as exc_info:
        enforce_valid_config(
            k_min=3,
            k_max=5,
            total_assets=15,
            max_weight=0.10
        )
    assert "Infeasible weight limit" in str(exc_info.value)
